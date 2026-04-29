from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero


class EstateProperty(models.Model):
    _name = 'estate.property'
    _description = 'Real Estate Property'
    _order = 'id desc'

    # -------------------------------------------------------------------------
    # Basic fields
    # -------------------------------------------------------------------------
    name = fields.Char(string='Title', required=True)
    description = fields.Text(string='Description')
    postcode = fields.Char(string='Postcode')
    date_availability = fields.Date(
        string='Available From',
        copy=False,
        default=lambda self: fields.Date.add(fields.Date.today(), months=3),
    )
    expected_price = fields.Float(string='Expected Price', required=True)
    selling_price = fields.Float(string='Selling Price', copy=False, readonly=True)
    bedrooms = fields.Integer(string='Bedrooms', default=2)
    living_area = fields.Integer(string='Living Area (sqm)')
    facades = fields.Integer(string='Facades')
    garage = fields.Boolean(string='Garage')
    garden = fields.Boolean(string='Garden')
    garden_area = fields.Integer(string='Garden Area (sqm)')
    garden_orientation = fields.Selection(
        selection=[
            ('north', 'North'),
            ('south', 'South'),
            ('east', 'East'),
            ('west', 'West'),
        ],
        string='Garden Orientation',
    )
    active = fields.Boolean(string='Active', default=True)
    state = fields.Selection(
        selection=[
            ('new', 'New'),
            ('offer_received', 'Offer Received'),
            ('offer_accepted', 'Offer Accepted'),
            ('sold', 'Sold'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        required=True,
        copy=False,
        default='new',
    )

    # -------------------------------------------------------------------------
    # Relational fields
    # -------------------------------------------------------------------------
    property_type_id = fields.Many2one(
        comodel_name='estate.property.type',
        string='Property Type',
    )
    salesperson_id = fields.Many2one(
        comodel_name='res.users',
        string='Salesperson',
        default=lambda self: self.env.user,
    )
    buyer_id = fields.Many2one(
        comodel_name='res.partner',
        string='Buyer',
        copy=False,
    )
    tag_ids = fields.Many2many(
        comodel_name='estate.property.tag',
        string='Tags',
    )
    offer_ids = fields.One2many(
        comodel_name='estate.property.offer',
        inverse_name='property_id',
        string='Offers',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )

    # -------------------------------------------------------------------------
    # Computed fields
    # -------------------------------------------------------------------------
    total_area = fields.Integer(
        string='Total Area (sqm)',
        compute='_compute_total_area',
    )
    best_price = fields.Float(
        string='Best Offer',
        compute='_compute_best_price',
    )

    # -------------------------------------------------------------------------
    # SQL Constraints (database level — fastest, no Python overhead)
    # -------------------------------------------------------------------------
    _sql_constraints = [
        (
            'check_expected_price_positive',
            'CHECK(expected_price > 0)',
            'The expected price must be strictly positive.',
        ),
        (
            'check_selling_price_non_negative',
            'CHECK(selling_price >= 0)',
            'The selling price must be positive.',
        ),
    ]

    # -------------------------------------------------------------------------
    # Compute methods
    # -------------------------------------------------------------------------
    @api.depends('living_area', 'garden_area')
    def _compute_total_area(self):
        for prop in self:
            prop.total_area = prop.living_area + prop.garden_area

    @api.depends('offer_ids.price')
    def _compute_best_price(self):
        for prop in self:
            prop.best_price = max(prop.offer_ids.mapped('price'), default=0.0)

    # -------------------------------------------------------------------------
    # Onchange
    # -------------------------------------------------------------------------
    @api.onchange('garden')
    def _onchange_garden(self):
        if self.garden:
            self.garden_area = 10
            self.garden_orientation = 'north'
        else:
            self.garden_area = 0
            self.garden_orientation = False

    # -------------------------------------------------------------------------
    # Python Constraints (cross-field logic — cannot be done in SQL)
    # -------------------------------------------------------------------------
    @api.constrains('selling_price', 'expected_price')
    def _check_selling_price(self):
        for prop in self:
            # Only validate when selling_price is actually set (not 0.0 default)
            if float_is_zero(prop.selling_price, precision_digits=2):
                continue
            if float_compare(
                prop.selling_price,
                prop.expected_price * 0.9,
                precision_digits=2,
            ) < 0:
                raise ValidationError(
                    'The selling price cannot be lower than 90%% of the expected price '
                    '(%s). Reduce the expected price if needed.'
                    % (prop.expected_price * 0.9)
                )

    # -------------------------------------------------------------------------
    # Actions
    # -------------------------------------------------------------------------
    def action_sold(self):
        for prop in self:
            if prop.state == 'cancelled':
                raise UserError('A cancelled property cannot be sold.')
            prop.state = 'sold'
        return True

    def action_cancel(self):
        for prop in self:
            if prop.state == 'sold':
                raise UserError('A sold property cannot be cancelled.')
            prop.state = 'cancelled'
        return True