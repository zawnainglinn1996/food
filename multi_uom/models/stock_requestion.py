from odoo import api, models, fields,_


class StockRequestionLine(models.Model):
    _inherit = 'stock.requestion.line'

    multi_uom_line_ids = fields.Many2many('multi.uom.line', compute='compute_multi_uom_line_ids')
    multi_uom_line_id = fields.Many2one('multi.uom.line', 'Multi UOM')
    product_multi_uom_qty = fields.Float('Multi Request Qty', default=1.0,
                                         digits='Product Unit of Measure', required=True, tracking=2)




    @api.depends('product_id')
    def compute_multi_uom_line_ids(self):
        for rec in self:
            rec.multi_uom_line_ids = []
            if rec.product_id.multi_uom_line_ids:
                rec.multi_uom_line_ids = rec.product_id.multi_uom_line_ids.ids

    @api.onchange('product_multi_uom_qty', 'product_id', 'multi_uom_line_id')
    def _change_multi_uom_qty(self):
        for rec in self:
            if rec.product_id and rec.product_multi_uom_qty and rec.multi_uom_line_id:
                rec.product_uom_qty = rec.multi_uom_line_id.ratio * rec.product_multi_uom_qty

    def _prepare_move_values(self, picking, requestion_type):
        values = super(StockRequestionLine, self)._prepare_move_values(picking, requestion_type)
        values['multi_uom_line_id'] = self.multi_uom_line_id.id
        return values

    @api.model
    def create(self, values):
        if values.get('display_type', self.default_get(['display_type'])['display_type']):
            values.update(product_id=False, product_uom_qty=0, multi_uom_line_id=False)
        return super(StockRequestionLine, self).create(values)

    @api.onchange('product_id')
    def onchange_product(self):
        res = super(StockRequestionLine, self).onchange_product()
        line = self.product_id.multi_uom_line_ids.filtered(lambda l: l.is_default_uom == True)
        self.multi_uom_line_id = line.id
        return res
