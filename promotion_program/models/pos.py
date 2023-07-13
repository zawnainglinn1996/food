from collections import defaultdict
from odoo import api, fields, models, _
from odoo.tools import float_is_zero


class PosOrder(models.Model):

    _inherit = 'pos.order'

    def _prepare_invoice_line(self, order_line):
        values = super()._prepare_invoice_line(order_line)
        values.update({
            'promotion_id': order_line.promotion_id.id,
            'promotion_account_id': order_line.promotion_account_id.id,
        })
        return values


class PosOrderLine(models.Model):

    _inherit = 'pos.order.line'

    promotion_id = fields.Many2one('promotion.program', 'Promotion')
    promotion_line_id = fields.Integer('Promotion Line ID')
    promotion_description = fields.Text('Promotion Description')
    promotion_account_id = fields.Many2one('account.account', 'Promotion COA')

    def _export_for_ui(self, orderline):
        values = super()._export_for_ui(orderline)
        values.update({
            'promotion_id': orderline.promotion_id.id,
            'promotion_line_id': orderline.promotion_line_id,
            'promotion_description': orderline.promotion_description,
        })
        return values


class PosSession(models.Model):

    _inherit = 'pos.session'

    def _create_picking_at_end_of_session(self):
        self.ensure_one()
        lines_grouped_by_dest_location = {}
        picking_type = self.config_id.picking_type_id

        if not picking_type or not picking_type.default_location_dest_id:
            session_destination_id = self.env['stock.warehouse']._get_partner_locations()[0].id
        else:
            session_destination_id = picking_type.default_location_dest_id.id

        for order in self.order_ids:
            if order.company_id.anglo_saxon_accounting and order.is_invoiced or order.to_ship:
                continue
            destination_id = order.partner_id.property_stock_customer.id or session_destination_id
            if destination_id in lines_grouped_by_dest_location:
                lines_grouped_by_dest_location[destination_id] |= order.lines
            else:
                lines_grouped_by_dest_location[destination_id] = order.lines

        for location_dest_id, lines in lines_grouped_by_dest_location.items():
            pickings = self.env['stock.picking']._create_picking_from_pos_order_lines(location_dest_id, lines, picking_type)
            pickings.write({'pos_session_id': self.id, 'origin': self.name})

    def _accumulate_amounts(self, data):
        data = super()._accumulate_amounts(data)
        if not self.company_id.anglo_saxon_accounting:
            return data
        amounts = lambda: {'amount': 0.0, 'amount_converted': 0.0}
        stock_expense = defaultdict(amounts)
        for order in self.order_ids.filtered(lambda o: not o.is_invoiced and o.picking_ids):
            stock_moves = self.env['stock.move'].sudo().search([
                ('picking_id', 'in', order.picking_ids.ids),
                ('company_id.anglo_saxon_accounting', '=', True),
                ('product_id.categ_id.property_valuation', '=', 'real_time')
            ])
            for move in stock_moves:
                if move.promotion_account_id:
                    exp_key = move.promotion_account_id
                else:
                    exp_key = move.product_id._get_product_accounts()['expense']
                amount = -sum(move.sudo().stock_valuation_layer_ids.mapped('value'))
                stock_expense[exp_key] = self._update_amounts(stock_expense[exp_key], {'amount': amount}, move.picking_id.date, force_company_currency=True)

        global_session_pickings = self.picking_ids.filtered(lambda p: not p.pos_order_id)
        if global_session_pickings:
            stock_moves = self.env['stock.move'].sudo().search([
                ('picking_id', 'in', global_session_pickings.ids),
                ('company_id.anglo_saxon_accounting', '=', True),
                ('product_id.categ_id.property_valuation', '=', 'real_time'),
            ])
            for move in stock_moves:
                if move.promotion_account_id:
                    exp_key = move.promotion_account_id
                else:
                    exp_key = move.product_id._get_product_accounts()['expense']
                amount = -sum(move.stock_valuation_layer_ids.mapped('value'))
                stock_expense[exp_key] = self._update_amounts(stock_expense[exp_key], {'amount': amount}, move.picking_id.date, force_company_currency=True)
        data.update({
            'stock_expense': stock_expense,
        })
        return data
