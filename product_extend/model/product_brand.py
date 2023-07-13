from odoo import models, fields, api, _


class ProductBrand(models.Model):
    _name = 'product.brand'
    _description = "Product Brand"

    name = fields.Char(string="Name")
    short_code = fields.Char(string='Short Code')

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'This Name Already Exit!'),
    ]

