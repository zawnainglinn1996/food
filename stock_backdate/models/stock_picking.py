from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _action_done(self):
        super(StockPicking, self)._action_done()
        if not self.sale_id:
            if self.scheduled_date:
                self.write({'date_done': self.scheduled_date, 'priority': '0'})
                self.move_line_ids.write({'date': self.scheduled_date})
                self.move_lines.write({'date': self.scheduled_date})


    @api.depends('move_lines.state', 'move_lines.date', 'move_type')
    def _compute_scheduled_date(self):
        for picking in self:
            moves_dates = picking.move_lines.filtered(lambda move: move.state not in ('done', 'cancel')).mapped('date')
            if picking.sale_requisition_id:
                picking.scheduled_date = picking.sale_requisition_id.scheduled_date
            elif picking.requestion_id:
                picking.scheduled_date = picking.requestion_id.scheduled_date
            else:
                if picking.move_type == 'direct':
                    picking.scheduled_date = min(moves_dates, default=picking.scheduled_date or fields.Datetime.now())
                elif picking.sale_id:
                    picking.scheduled_date = picking.sale_id.backdate
                elif picking.purchase_id:
                    picking.scheduled_date = picking.purchase_id.date_order
                elif picking.picking_type_code in ('incoming', 'incoming', 'internal'):
                    picking.scheduled_date = picking.scheduled_date
                else:
                    picking.scheduled_date = max(moves_dates, default=picking.scheduled_date or fields.Datetime.now())

