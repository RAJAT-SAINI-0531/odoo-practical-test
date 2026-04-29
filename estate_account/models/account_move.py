from odoo import fields, models


class AccountMove(models.Model):
    """
    Extend account.move to store the originating estate property.
    This is the FK that lets estate.property find its invoices.
    """
    _inherit = 'account.move'

    estate_property_id = fields.Many2one(
        comodel_name='estate.property',
        string='Estate Property',
        ondelete='set null',
        copy=False,
        index=True,  # fast search when filtering invoices by property
    )