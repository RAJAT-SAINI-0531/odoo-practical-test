from odoo import api, fields, models


class EstatePropertyType(models.Model):
    _name = 'estate.property.type'
    _description = 'Real Estate Property Type'
    _order = 'sequence, name'

    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)

    property_ids = fields.One2many(
        comodel_name='estate.property',
        inverse_name='property_type_id',
        string='Properties',
    )
    # offer_ids works because estate.property.offer stores property_type_id
    # as a stored related field (see estate_property_offer.py)
    offer_ids = fields.One2many(
        comodel_name='estate.property.offer',
        inverse_name='property_type_id',
        string='Offers',
    )
    offer_count = fields.Integer(
        string='Offer Count',
        compute='_compute_offer_count',
    )

    _sql_constraints = [
        (
            'unique_property_type_name',
            'UNIQUE(name)',
            'A property type with this name already exists.',
        ),
    ]

    @api.depends('offer_ids')
    def _compute_offer_count(self):
        for ptype in self:
            ptype.offer_count = len(ptype.offer_ids)