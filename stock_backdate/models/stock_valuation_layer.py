from odoo import fields, models, tools


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    date = fields.Datetime('Date')

    def init(self):
        tools.create_index(
            self._cr, 'stock_valuation_layer_index',
            self._table, ['product_id', 'remaining_qty', 'stock_move_id', 'company_id', 'create_date', 'date']
        )