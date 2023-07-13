import datetime
from odoo import models, fields, api, _
from datetime import timedelta


class SubmissionQuotation(models.Model):
    _inherit = 'submission.quotation'

    def get_submission_quotation_a4(self):
        index = 1
        records = []

        for order in self:
            submission_line_ids = []
            for line in order.submission_line_ids:
                submission_line_ids.append({
                    'sr': index,
                    'pur_agree_id': line.purchase_agreement_id.name or '',
                    'supplier': line.supplier_id.name or '',
                    'product': line.product_id.name or '',
                    'brand': line.brand_id.name or '',
                    'uom': line.product_id.uom_id.name or '',
                    'allow_qty': "{:,.0f}".format(line.allowed_qty) or 0.00,
                    'require_qty': "{:,.0f}".format(line.required_qty) or 0.00,
                    'currency': line.currency_id.name or '',
                    'price_unit': "{:,.0f}".format(line.price_unit) or 0.00,
                    'dis_amt': "{:,.0f}".format(line.discount_amount) or 0.00,
                    'tax': line.taxes_id.name or '',
                    'other_charges': line.other_charges or '0',
                    'payment_term': line.property_supplier_payment_term_id.name or '',
                    'subtotal': "{:,.0f}".format(line.amount_mmk) or 0.00,
                    'con_to_pur': line.confirm_to_purchase or False,
                })
                index += 1

            records.append({
                'sq_no': order.reference_code or '',
                # 'date': (order.date_approve + timedelta(hours=6, minutes=30)).strftime("%d/%m/%Y") or '',
                'prepared_by_sign': order.prepare_by_sign or '',
                'prepared_by_date': order.prepare_by_date or '',
                'prepared_by_name': order.prepare_by_name.name or '',
                'confirm_by_sign': order.confirm_by_sign or '',
                'confirm_by_date': order.confirm_by_date or '',
                'confirm_by_name': order.confirm_by_name.name or '',
                'checked_by_sign': order.verified_by_sign or '',
                'checked_by_date': order.verified_by_date or '',
                'checked_by_name': order.verified_by_name.name or '',
                'approved_by_sign': order.approved_by_sign or '',
                'approved_by_date': order.approved_by_date or '',
                'approved_by_name': order.approved_by_name.name or '',
                'submission_line_ids': submission_line_ids or '',
            })
        return self.env.ref('report_form.action_submission_quotation_pdf_report').report_action(self, data={
            'records': records})
