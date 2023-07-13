from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class StockMove(models.Model):
    _inherit = 'stock.move'

    standard_quantity = fields.Float(string='Standard Qty', compute='_compute_standard_qty', digits='Product Unit of Measure', default=0.0, store=True)
    difference_quantity = fields.Float(string='Difference Qty', compute='compute_difference_qty', digits='Product Unit of Measure', default=0.0,
                                       store=True)
    real_product_qty = fields.Float(string='Real Product Qty')

    @api.depends('real_product_qty', 'move_lines_count')
    def _compute_standard_qty(self):
        for rec in self:
            if rec.real_product_qty:
                rec.standard_quantity = rec.real_product_qty
            if rec.real_product_qty and rec.move_lines_count == 0:
                rec.standard_quantity = 0

    @api.depends('quantity_done', 'standard_quantity', 'move_lines_count')
    def compute_difference_qty(self):
        for rec in self:
            if rec.multi_quantity_done or rec.standard_quantity:
                rec.difference_quantity = rec.multi_quantity_done - rec.standard_quantity
            if rec.move_lines_count == 0:
                rec.difference_quantity = 0

    def _set_quantity_done_prepare_vals(self, qty):
        res = []

        for ml in self.move_line_ids:
            ml_qty = ml.product_uom_qty - ml.qty_done
            if float_compare(ml_qty, 0, precision_rounding=ml.product_uom_id.rounding) <= 0:
                continue
            # Convert move line qty into move uom
            if ml.product_uom_id != self.product_uom:
                ml_qty = ml.product_uom_id._compute_quantity(ml_qty, self.product_uom, round=False)

            taken_qty = min(qty, ml_qty)
            # Convert taken qty into move line uom
            if ml.product_uom_id != self.product_uom:
                taken_qty = self.product_uom._compute_quantity(ml_qty, ml.product_uom_id, round=False)

            # Assign qty_done and explicitly round to make sure there is no inconsistency between
            # ml.qty_done and qty.
            taken_qty = float_round(taken_qty, precision_rounding=ml.product_uom_id.rounding)
            res.append((1, ml.id, {'qty_done': ml.qty_done + taken_qty}))
            if ml.product_uom_id != self.product_uom:
                taken_qty = ml.product_uom_id._compute_quantity(ml_qty, self.product_uom, round=False)
            qty -= taken_qty

            if float_compare(qty, 0.0, precision_rounding=self.product_uom.rounding) <= 0:
                break

        for ml in self.move_line_ids:
            if float_is_zero(ml.product_uom_qty, precision_rounding=ml.product_uom_id.rounding) and float_is_zero(
                    ml.qty_done, precision_rounding=ml.product_uom_id.rounding):
                res.append((2, ml.id))

        if float_compare(qty, 0.0, precision_rounding=self.product_uom.rounding) > 0:
            if self.product_id.tracking != 'serial':
                vals = self._prepare_move_line_vals(quantity=0)
                vals['qty_done'] = qty
                vals['multi_qty_done'] = qty
                res.append((0, 0, vals))
            else:
                uom_qty = self.product_uom._compute_quantity(qty, self.product_id.uom_id)
                for i in range(0, int(uom_qty)):
                    vals = self._prepare_move_line_vals(quantity=0)
                    vals['qty_done'] = 1
                    vals['product_uom_id'] = self.product_id.uom_id.id
                    res.append((0, 0, vals))
        return res
