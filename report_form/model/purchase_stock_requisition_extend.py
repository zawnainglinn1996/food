import datetime
from odoo import models, fields, api, _
from datetime import timedelta

class PurchaseStockRequisition(models.Model):
    _inherit = 'purchase.stock.requisition'

    def get_purchase_stock_requisition_a4(self):
        index = 1
        records = []

        for order in self:

            purchase_requisition_line = []
            for line in order.purchase_requisition_line:
                product_period = ''
                if line.product_period == '1':
                    product_period = 'Months'
                elif line.product_period == '12':
                    product_period = 'Years'
                purchase_requisition_line.append({
                    'sr': index,
                    'product': line.product_id.name or '',
                    'brand': line.brand_id.name or '',
                    'description': line.product_id.name or '',
                    'uom': line.product_id.uom_id.name or '',
                    'require_qty': line.required_qty or '0',
                    'allow_qty': line.allowed_qty or '0',
                    'lifecycle_period': line.product_warranty_period or '0',
                    'product_period': product_period or '',
                    'expected_date': (line.expected_date + timedelta(hours=6, minutes=30)).strftime("%d/%m/%Y") or '',
                    'remark': line.remark or '',
                })
                index += 1

            records.append({
                    'req_date': (order.request_date + timedelta(hours=6, minutes=30)).strftime("%d/%m/%Y") or '',
                    'req_department': order.department_id.complete_name or '',
                    'prf_no': order.reference_code or '',
                    'req_by_sign': order.req_by_sign,
                    'req_by_date': order.req_by_date,
                    'req_by_name': order.req_by_name.name,
                    'verified_by_sign': order.verified_by_sign,
                    'verified_by_date': order.verified_by_date,
                    'verified_by_name': order.verified_by_name.name,
                    'check_by_sign': order.check_by_sign,
                    'check_by_date': order.check_by_date,
                    'check_by_name': order.check_by_name.name,
                    'approved_by_sign': order.approved_by_sign,
                    'approved_by_date': order.approved_by_date,
                    'approved_by_name': order.approved_by_name.name,
                    'purchase_requisition_line': purchase_requisition_line,
                })
        return self.env.ref('report_form.action_purchase_stock_requisition_pdf_report').report_action(self, data={'records': records})
