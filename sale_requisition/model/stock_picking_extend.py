from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    sale_requisition_id = fields.Many2one('whole.sale.requisition', string='Sale Requestion',copy=False)
    is_already_sale_requisition = fields.Boolean(string='Already Requested',copy=False)

    @api.depends('move_lines.state', 'move_lines.date', 'move_type')
    def _compute_scheduled_date(self):
        for picking in self:
            moves_dates = picking.move_lines.filtered(lambda move: move.state not in ('done', 'cancel')).mapped('date')
            if not picking.is_good_received or not picking.is_good_issued:
                if picking.move_type == 'direct':
                    picking.scheduled_date = picking.date
                else:
                    picking.scheduled_date = picking.date
            else:
                if picking.move_type == 'direct':
                    picking.scheduled_date = min(moves_dates, default=picking.scheduled_date or fields.Datetime.now())
                else:
                    picking.scheduled_date = max(moves_dates, default=picking.scheduled_date or fields.Datetime.now())


class StockMove(models.Model):
    _inherit = 'stock.move'

    ws_req_line_id = fields.Many2one('whole.sale.requisition.line', string='Stock Req ')

    def _action_done(self, cancel_backorder=False):
        res = super(StockMove, self)._action_done(cancel_backorder)
        for rec in self:
            if rec.requestion_type == 'issued':
                prev_qty = rec.ws_req_line_id.issued_qty
                if rec.location_id.usage == 'internal' and rec.location_dest_id.usage == 'transit':
                    sign = 1
                else:
                    sign = -1
                done_quantity = rec.quantity_done * sign
                rec.ws_req_line_id.issued_qty = done_quantity + prev_qty
            elif rec.requestion_type == 'received':
                prev_qty = rec.ws_req_line_id.received_qty
                if rec.location_id.usage == 'transit' and rec.location_dest_id.usage == 'internal':
                    sign = 1
                else:
                    sign = -1
                done_quantity = rec.quantity_done * sign
                rec.ws_req_line_id.received_qty = done_quantity + prev_qty

        return res


