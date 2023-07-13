from odoo import api, models, fields
from itertools import groupby


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    def _create_move_from_pos_order_lines(self, lines):
        self.ensure_one()
        grouped_lines = {}
        for line in lines:
            key = f'{line.product_id.id}-{line.promotion_account_id.id}'
            existing_lines = grouped_lines.get(key, [])
            existing_lines.append(line)
            grouped_lines[key] = existing_lines
        move_vals = []
        for key, olines in grouped_lines.items():
            order_lines = self.env['pos.order.line'].concat(*olines)
            move_vals.append(self._prepare_stock_move_vals(order_lines[0], order_lines))
        moves = self.env['stock.move'].create(move_vals)
        confirmed_moves = moves._action_confirm()
        confirmed_moves._add_mls_related_to_order(lines, are_qties_done=True)

    def _prepare_stock_move_vals(self, first_line, order_lines):
        values = super()._prepare_stock_move_vals(first_line, order_lines)
        values.update({
            'promotion_account_id': first_line.promotion_account_id.id,
        })
        return values
