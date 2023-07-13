import datetime
from odoo import models, fields, api, _
from datetime import timedelta

class StockRequestion(models.Model):
    _inherit = 'stock.requestion'

    def get_stock_requestion(self):
        index = 1
        records = []

        for order in self:
            stock_requestion_line = []
            for requestion_line in order.stock_requestion_line:
                stock_requestion_line.append({
                    'sr': index,
                    'product': requestion_line.product_id.name or '',
                    'brand': requestion_line.product_id.brand_id.name or '',
                    'description': requestion_line.product_id.name or '',
                    'uom': requestion_line.product_id.uom_id.name or '',
                    'req_qty': requestion_line.product_uom_qty or '0',
                    'issued_qty': requestion_line.issued_qty or '0',
                    'received_qty': requestion_line.received_qty or '0',
                    'scheduled_date':  (requestion_line.scheduled_date + timedelta(hours=6, minutes=30)).strftime("%d/%m/%Y") if requestion_line.scheduled_date else '',
                    'reason': requestion_line.reason or '',
                    'remark': requestion_line.remark or '',
                })
                index += 1

            records.append({
                    'document_no': order.document_no or '',
                    'created_date': (order.created_date + timedelta(hours=6, minutes=30)).strftime("%d/%m/%Y") or '',
                    'request_from': order.request_from.complete_name or '',
                    'request_to': order.request_to.complete_name or '',
                    'req_by_sign': order.req_by_sign or '',
                    'req_by_name': order.req_by_name.name or '',
                    'approved_by_sign': order.approved_by_sign or '',
                    'approved_by_name': order.approved_by_name.name or '',
                    'verified_by_sign': order.verified_by_sign or '',
                    'verified_by_name': order.verified_by_name.name or '',
                    'confirm_by_sign': order.confirm_by_sign or '',
                    'confirm_by_name': order.confirm_by_name.name or '',
                    'stock_requestion_line': stock_requestion_line,
                })
        return self.env.ref('report_form.action_stock_requestion_pdf_report').report_action(self, data={'records': records})
