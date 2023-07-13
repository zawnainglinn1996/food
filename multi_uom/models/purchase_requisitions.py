from odoo import api, models, fields, _
from odoo.fields import Date
from itertools import groupby


class PurchaseRequisitionLine(models.Model):
    _inherit = "purchase.requisitions.line"

    multi_uom_line_ids = fields.Many2many('multi.uom.line', compute='compute_multi_uom_line_ids')
    multi_uom_line_id = fields.Many2one('multi.uom.line', 'Multi UoM')
    multi_required_qty = fields.Float(string='Multi Quantity', digits='Product Unit of Measure')
    multi_allowed_qty = fields.Float(string='Multi Allowed Quantity', digits='Product Unit of Measure')

    @api.depends('product_id')
    def compute_multi_uom_line_ids(self):
        for rec in self:
            rec.multi_uom_line_ids = []
            if rec.product_id.multi_uom_line_ids:
                rec.multi_uom_line_ids = rec.product_id.multi_uom_line_ids.ids

    @api.onchange('product_id')
    def product_id_change(self):
        for rec in self:
            if rec.product_id:
                line = rec.product_id.multi_uom_line_ids.filtered(lambda l: l.is_default_uom == True)
                rec.multi_uom_line_id = line

    @api.onchange('product_id', 'multi_required_qty', 'multi_uom_line_id')
    def change_required_qty(self):
        for rec in self:
            if rec.product_id and rec.multi_uom_line_id and rec.multi_required_qty:
                rec.required_qty = rec.multi_uom_line_id.ratio * rec.multi_required_qty
                if rec.multi_allowed_qty:
                    rec.allowed_qty = rec.multi_uom_line_id.ratio * rec.multi_allowed_qty

    @api.onchange('product_id', 'multi_allowed_qty', 'multi_uom_line_id')
    def change_allowed_qty(self):
        for rec in self:
            if rec.product_id and rec.multi_uom_line_id and rec.multi_allowed_qty:
                rec.allowed_qty = rec.multi_uom_line_id.ratio * rec.multi_allowed_qty

    def action_purchase_agreement(self):
        agreement_lines = []
        active_ids = self.env.context.get('active_ids', [])
        lines = self.env['purchase.requisitions.line'].browse(active_ids)
        lines = lines.sorted(key=lambda l: (l.product_id.id, l.multi_uom_line_id.id))
        purchase_agreement = self.env['purchase.requisition'].create({
            'ordering_date': Date.today(),

        })
        is_created = False
        for key, grouped_lines in groupby(lines, lambda l: (l.product_id.id, l.multi_uom_line_id.id)):
            allowed_qty = 0
            req_qty = 0
            multi_allowed_qty = 0
            multi_required_qty = 0
            first_line = False
            for line in grouped_lines:
                multi_allowed_qty += line.multi_allowed_qty
                multi_required_qty += line.multi_required_qty
                allowed_qty += line.multi_allowed_qty
                req_qty += line.multi_required_qty
                first_line = line
            if not first_line.product_id:
                continue
            agreement_lines.append({
                'product_id': first_line.product_id.id,
                'product_description_variants': first_line.name,
                'required_qty': req_qty,
                'product_qty': allowed_qty,
                'product_uom_id': first_line.product_uom.id,
                'multi_uom_line_id': first_line.multi_uom_line_id.id,
                'schedule_date': first_line.expected_date,
                'requisition_id': purchase_agreement.id,
                'product_warranty_period': first_line.product_warranty_period,
                'product_period': first_line.product_period,
                'remark': first_line.remark
            })

        purchase_requisition_line_id = self.env['purchase.requisition.line'].create(agreement_lines)

        if purchase_requisition_line_id:
            is_created = True
        if is_created:
            for line in lines:
                line.write({
                    'is_created_aggrement': True,
                })
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': 'Converted To Purchase Agreement',
                    'type': 'rainbow_man',
                }
            }
