from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import groupby


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_create_done = fields.Boolean(string='Is Converted to Requisition', default=False, copy=False)

    requisition_status = fields.Selection([('requisition', 'Requisition'), ('not_request', 'Not Requisition')],
                                          string='Requisition Status', compute='_get_req_status')

    @api.depends('is_create_done')
    def _get_req_status(self):
        for rec in self:
            if rec.is_create_done:
                rec.requisition_status = 'requisition'
            else:
                rec.requisition_status = 'not_request'

    def action_sale_requisition(self):
        self.is_create_done = True
        order_lines = []
        active_ids = self.env.context.get('active_ids', [])
        active_sale_order = self.env['sale.order'].browse(active_ids)
        lines = self.order_line.filtered(
            lambda line: not line.display_type and line.product_id.detailed_type != 'service')
        line = lines.sorted(key=lambda l: (l.product_id.id, l.product_uom.id))
        whole_sale_requisition = self.env['whole.sale.requisition'].create({
            'analytic_account_id': self.analytic_account_id.id,
            'company_id': self.env.company.id,
            'is_whole_sale': True,
            'from_location_id': self.warehouse_id.lot_stock_id.id,
            'scheduled_date': self.commitment_date,
            'sale_order_id': self.id,
            'partner_id': self.partner_id.id,
            'sale_picking': self.sale_picking,
        })

        for key, grouped_lines in groupby(line, lambda l: (l.product_id.id, l.product_uom.id)):
            req_qty = 0
            all_remark = ''
            first_line = False
            for line in grouped_lines:
                req_qty += line.multi_uom_qty
                if line.remark:
                    all_remark += line.remark
                else:
                    line.remark = ''
                first_line = line
            order_lines.append({
                'product_id': first_line.product_id.id,
                'name': first_line.name,
                'required_qty': req_qty,
                'product_uom_id': first_line.product_uom.id,
                'requisition_id': whole_sale_requisition.id,
                'multi_uom_line_id': first_line.multi_uom_line_id.id,
                'packaging_size': first_line.product_packaging_qty,
                'remark': all_remark
            })

        self.env['whole.sale.requisition.line'].create(order_lines)
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Successfully Converted To Whole Sale Requisition',
                'type': 'rainbow_man',
            }
        }


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id', 'product_uom_qty', 'product_uom')
    def _onchange_suggest_packaging(self):
        # remove packaging if not match the pro
        # duct
        if self.product_packaging_id.product_id != self.product_id:
            self.product_packaging_id = False

        # # suggest biggest suitable packaging
        # if self.product_id and self.product_uom_qty and self.product_uom:
        #     self.product_packaging_id = self.product_id.packaging_ids.filtered(
        #         'sales')._find_suitable_product_packaging(self.product_uom_qty, self.product_uom)
