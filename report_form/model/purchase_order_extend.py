import datetime
from odoo import models, fields, api, _
from datetime import timedelta


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def get_purchase_order_a4(self):
        index = 1
        records = []

        for order in self:
            order_line = []
            for line in order.order_line:
                order_line.append({
                    'sr': index,
                    'product': line.product_id.name or '',
                    'description': line.product_id.name or '',
                    'deli_date': (line.date_planned + timedelta(hours=6, minutes=30)).strftime(
                        "%d/%m/%Y") if line.date_planned else '',
                    'qty': "{:,.0f}".format(line.product_qty) or 0.00,
                    'uom': line.product_id.uom_id.name or '',
                    'pack_qty': line.product_packaging_qty or 0.00,
                    'price_unit': "{:,.0f}".format(line.price_unit) or 0.00,
                    'dis_amt': line.discount_amount or 0.00,
                    'tax': line.taxes_id.name or 0.00,
                    'subtotal': "{:,.0f}".format(line.price_subtotal) or 0.00,
                })
                index += 1

            records.append({
                'po_no': order.name or '',
                'date': (order.date_order + timedelta(hours=6, minutes=30)).strftime(
                    "%d/%m/%Y") if order.date_order else '',
                'supplier_name': order.partner_id.name or '',
                'sq_no': order.submission_no or '',
                'deli_to': order.picking_type_id.warehouse_id.name + ': ' + order.picking_type_id.name,
                'prepared_by_sign': order.prepare_by_sign,
                'prepared_by_date': order.prepare_by_date,
                'prepared_by_name': order.prepare_by_name.name,
                'confirm_by_sign': order.confirm_by_sign,
                'confirm_by_date': order.confirm_by_date,
                'confirm_by_name': order.confirm_by_name.name,
                'verified_by_sign': order.verified_by_sign,
                'verified_by_date': order.verified_by_date,
                'verified_by_name': order.verified_by_name.name,
                'approved_by_sign': order.approved_by_sign,
                'approved_by_date': order.approved_by_date,
                'approved_by_name': order.approved_by_name.name,
                'order_line': order_line,
            })
        return self.env.ref('report_form.action_purchase_order_pdf_report').report_action(self,
                                                                                          data={'records': records})
