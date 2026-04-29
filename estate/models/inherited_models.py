from odoo import fields, models


class ResUsers(models.Model):
    """Extend res.users to surface the salesperson's active properties."""
    _inherit = 'res.users'

    property_ids = fields.One2many(
        comodel_name='estate.property',
        inverse_name='salesperson_id',
        string='Properties',
        domain=[('state', 'not in', ('sold', 'cancelled'))],
    )


class ResPartner(models.Model):
    """Extend res.partner to surface offers made by this partner."""
    _inherit = 'res.partner'

    offer_ids = fields.One2many(
        comodel_name='estate.property.offer',
        inverse_name='partner_id',
        string='Real Estate Offers',
    )