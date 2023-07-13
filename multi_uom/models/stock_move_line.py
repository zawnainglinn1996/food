from odoo import api, models, fields, _


class StockMoveLine(models.Model):

    _inherit = 'stock.move.line'

    multi_uom_line_id = fields.Many2one('multi.uom.line', 'UOM', related='move_id.multi_uom_line_id', store=True)
    product_uom_qty = fields.Float(compute='compute_multi_product_uom_qty',
                                   inverse='_set_multi_product_uom_qty',
                                   store=True)
    qty_done = fields.Float(compute='compute_multi_qty_done',
                            inverse='_set_multi_qty_done',
                            store=True)
    multi_uom_qty = fields.Float('Reserved Qty', default=0.0, digits='Product Unit of Measure', required=True, copy=False)
    multi_qty_done = fields.Float('Done Qty', default=0.0, digits='Product Unit of Measure', copy=False)
    multi_uom_line_ids = fields.Many2many('multi.uom.line', compute='compute_multi_uom_line_ids')

    @api.depends('product_id')
    def compute_multi_uom_line_ids(self):
        for rec in self:
            rec.multi_uom_line_ids = rec.product_id.multi_uom_line_ids.ids

    @api.model
    def create(self, values):
        values['multi_uom_line_id'] = self.env['stock.move'].browse(values.get('move_id')).multi_uom_line_id.id
        return super(StockMoveLine, self).create(values)

    @api.depends('multi_uom_line_id', 'multi_uom_qty')
    def compute_multi_product_uom_qty(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.product_uom_qty = rec.multi_uom_qty * rec.multi_uom_line_id.ratio
            else:
                rec.product_uom_qty = 0

    @api.depends('multi_uom_line_id', 'multi_qty_done')
    def compute_multi_qty_done(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.qty_done = rec.multi_qty_done * rec.multi_uom_line_id.ratio
            else:
                rec.qty_done = 0

    def _set_multi_product_uom_qty(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.multi_uom_qty = rec.product_uom_qty / rec.multi_uom_line_id.ratio

    def _set_multi_qty_done(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.multi_qty_done = rec.qty_done / rec.multi_uom_line_id.ratio
