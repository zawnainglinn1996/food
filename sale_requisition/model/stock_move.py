from odoo import models, fields, api, _


class StockMove(models.Model):
    _inherit = 'stock.move'

    packaging_size = fields.Float(string='Packaging Size', default=0.0)
