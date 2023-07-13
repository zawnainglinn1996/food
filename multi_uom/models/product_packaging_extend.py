from odoo import models, fields, api, _


class ProductPackaging(models.Model):
    _inherit = 'product.packaging'

    multi_uom_line_id = fields.Many2one('multi.uom.line', 'UoM')



