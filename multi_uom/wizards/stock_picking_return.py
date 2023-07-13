from odoo import api, models, fields, _


class ReturnPicking(models.TransientModel):

    _inherit = 'stock.return.picking'

    @api.model
    def _prepare_stock_return_picking_line_vals_from_move(self, stock_move):
        values = super(ReturnPicking, self)._prepare_stock_return_picking_line_vals_from_move(stock_move)
        qty = values['quantity']
        values['multi_uom_qty'] = qty / stock_move.multi_uom_line_id.ratio
        return values


class ReturnPickingLine(models.TransientModel):

    _inherit = "stock.return.picking.line"

    quantity = fields.Float(compute='_compute_multi_uom_qty', inverse='_set_multi_uom_qty', store=True)
    multi_uom_qty = fields.Float("Qty", digits='Product Unit of Measure')
    multi_uom_line_id = fields.Many2one('multi.uom.line', string='UoM', related='move_id.multi_uom_line_id', store=True)

    @api.depends('move_id', 'multi_uom_line_id', 'multi_uom_qty')
    def _compute_multi_uom_qty(self):
        for rec in self:
            rec.quantity = rec.multi_uom_qty * rec.multi_uom_line_id.ratio

    def _set_multi_uom_qty(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.multi_uom_qty = rec.quantity / rec.multi_uom_line_id.ratio
            else:
                rec.multi_uom_qty = rec.quantity
