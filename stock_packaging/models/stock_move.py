from odoo import api, models, fields


class StockMove(models.Model):

    _inherit = 'stock.move'

    stock_packaging_line_id = fields.Many2one('stock.packaging.line', 'Packaging Line')

    def _get_price_unit(self):
        if self.stock_packaging_line_id:
            price_unit = self.stock_packaging_line_id.unit_cost
        else:
            price_unit = super()._get_price_unit()
        return price_unit
