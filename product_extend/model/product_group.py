from odoo import models, fields, api, _


class ProductGroup(models.Model):
    _name = 'product.group'
    _description = 'Product Group'

    name = fields.Char(string="Name")

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'This Name Already Exit!'),
    ]
