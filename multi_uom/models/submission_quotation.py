from odoo import models, fields, api, _


class SubmissionOfQuotationLine(models.Model):
    _inherit = 'submission.quotation.line'

    multi_uom_line_id = fields.Many2one('multi.uom.line', 'Multi UoM')
    uom_ratio_remark = fields.Char(string='Ratio Remark', related='multi_uom_line_id.remark')
    multi_uom_line_ids = fields.Many2many('multi.uom.line', compute='compute_multi_uom_line_ids')

    @api.depends('product_id')
    def compute_multi_uom_line_ids(self):
        for rec in self:
            rec.multi_uom_line_ids = rec.product_id.multi_uom_line_ids.ids





