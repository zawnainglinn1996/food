import logging
import re

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression


class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    multi_uom_line_id = fields.Many2one('multi.uom.line', 'Multi UOM Line', compute=False)
    multi_uom_line_ids = fields.Many2many('multi.uom.line', compute='compute_multi_uom_line_ids')

    @api.depends('product_tmpl_id')
    def compute_multi_uom_line_ids(self):
        for rec in self:
            rec.multi_uom_line_ids = rec.product_tmpl_id.multi_uom_line_ids.ids

    @api.onchange('product_tmpl_id')
    def onchange_product_tmpl(self):
        if self.product_tmpl_id:
            self.multi_uom_line_id = self.product_tmpl_id.multi_uom_line_ids.filtered \
                (lambda l: l.uom_id.id == self.product_tmpl_id.uom_po_id.id).id


