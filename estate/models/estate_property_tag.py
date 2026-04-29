from odoo import fields, models


class EstatePropertyTag(models.Model):
    _name = 'estate.property.tag'
    _description = 'Real Estate Property Tag'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
    color = fields.Integer(string='Color Index')

    _sql_constraints = [
        (
            'unique_tag_name',
            'UNIQUE(name)',
            'A tag with this name already exists.',
        ),
    ]