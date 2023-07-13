from odoo import models, fields, api, _


class WholeSaleRequisitionLine(models.Model):
    _inherit = 'whole.sale.requisition.line'

    multi_uom_line_id = fields.Many2one('multi.uom.line', 'UoM')
    uom_ratio_remark = fields.Char(string='Ratio Remark', related='multi_uom_line_id.remark')
    multi_uom_line_ids = fields.Many2many('multi.uom.line', compute='compute_multi_uom_line_ids')

    @api.depends('product_id')
    def compute_multi_uom_line_ids(self):
        for rec in self:
            rec.multi_uom_line_ids = rec.product_id.multi_uom_line_ids.ids

    @api.onchange('product_id')
    def onchange_product(self):
        res = super(WholeSaleRequisitionLine, self).onchange_product()
        line = self.product_id.multi_uom_line_ids.filtered(lambda l: l.is_default_uom == True)
        self.multi_uom_line_id = line.id
        return res

    def _prepare_move_values(self, picking, requestion_type):
        res = super(WholeSaleRequisitionLine, self)._prepare_move_values(picking,requestion_type)
        res.update({
            'multi_uom_line_id':self.multi_uom_line_id.id,
        })
        return res








