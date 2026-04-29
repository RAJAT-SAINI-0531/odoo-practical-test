from odoo import api, fields, models
from odoo.exceptions import UserError


class EstatePropertyOffer(models.Model):
    _name = 'estate.property.offer'
    _description = 'Real Estate Property Offer'
    _order = 'price desc'

    price = fields.Float(string='Price', required=True)
    status = fields.Selection(
        selection=[
            ('accepted', 'Accepted'),
            ('refused', 'Refused'),
        ],
        string='Status',
        copy=False,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=True,
    )
    property_id = fields.Many2one(
        comodel_name='estate.property',
        string='Property',
        required=True,
        ondelete='cascade',
    )
    # Stored related field: lets estate.property.type have a direct One2many
    # to offers WITHOUT a custom foreign key model. Standard Odoo pattern.
    property_type_id = fields.Many2one(
        related='property_id.property_type_id',
        string='Property Type',
        store=True,
    )
    validity = fields.Integer(string='Validity (days)', default=7)
    date_deadline = fields.Date(
        string='Deadline',
        compute='_compute_date_deadline',
        inverse='_inverse_date_deadline',
        store=True,
    )

    _sql_constraints = [
        (
            'check_offer_price_positive',
            'CHECK(price > 0)',
            'The offer price must be strictly positive.',
        ),
    ]

    # -------------------------------------------------------------------------
    # Compute / Inverse
    # -------------------------------------------------------------------------
    @api.depends('validity', 'create_date')
    def _compute_date_deadline(self):
        for offer in self:
            base = (
                offer.create_date.date()
                if offer.create_date
                else fields.Date.today()
            )
            offer.date_deadline = fields.Date.add(base, days=offer.validity)

    def _inverse_date_deadline(self):
        for offer in self:
            base = (
                offer.create_date.date()
                if offer.create_date
                else fields.Date.today()
            )
            offer.validity = (offer.date_deadline - base).days

    # -------------------------------------------------------------------------
    # ORM override: enforce business rules at creation
    # -------------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            prop = self.env['estate.property'].browse(vals['property_id'])
            if prop.state in ('sold', 'cancelled'):
                raise UserError(
                    'Cannot make an offer on a %s property.' % prop.state
                )
            # Refuse offers lower than current best
            if vals.get('price', 0) < prop.best_price:
                raise UserError(
                    'Offer price must be higher than the current best offer: %.2f'
                    % prop.best_price
                )
            # Transition state to "Offer Received" if still "New"
            if prop.state == 'new':
                prop.state = 'offer_received'
        return super().create(vals_list)

    # -------------------------------------------------------------------------
    # Actions
    # -------------------------------------------------------------------------
    def action_accept(self):
        for offer in self:
            if 'accepted' in offer.property_id.offer_ids.mapped('status'):
                raise UserError(
                    'An offer has already been accepted for property "%s".'
                    % offer.property_id.name
                )
            offer.status = 'accepted'
            offer.property_id.write({
                'buyer_id': offer.partner_id.id,
                'selling_price': offer.price,
                'state': 'offer_accepted',
            })
        return True

    def action_refuse(self):
        self.write({'status': 'refused'})
        return True