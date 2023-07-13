from odoo import models, fields, api, _


class ProductFamily(models.Model):
    _name = 'product.family'
    _description = 'Product Family'

    name = fields.Char(string="Name")

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'This Name Already Exit!'),
    ]
