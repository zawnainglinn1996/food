from odoo import models, fields, api, _


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    is_main_wh = fields.Boolean(string='Main Warehouse',default=False)
