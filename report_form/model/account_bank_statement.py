import datetime
from odoo import models, fields, api, _
from datetime import timedelta
from datetime import datetime


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    code = fields.Char('Code')

    @api.model
    def create(self, vals):
        short_code = self.env.company.short_code
        vals['code'] = str(short_code) + '/' + self.env['ir.sequence'].next_by_code(
            'bank.statement.code') or _('')
        res = super(AccountBankStatement, self).create(vals)
        return res

    def get_statement_payment_report(self):
        records = []
        line = []
        total = 0
        date = ''
        if self.line_ids:
            for lines in self.line_ids:
                line.append({
                    'p_ref': lines.payment_ref or '',
                    'amount': "{:,}".format(lines.amount) if lines.amount else '0',
                })
                total += lines.amount

        if self.date:
            date = (self.date + timedelta(hours=6, minutes=30)).strftime("%d-%m-%Y")

        records.append({
            'phone': self.company_id.phone or '',
            'mail': self.company_id.email or '',
            'website': self.company_id.website or '',
            'street': self.company_id.street or '',
            'street1': self.company_id.street2 or '',
            'country': self.company_id.country_id.name if self.company_id.country_id else '',
            'city': self.company_id.city or '',
            'state': self.company_id.state_id.name if self.company_id.state_id else '',
            'ref': self.name or '',
            'date':  date,
            'code': self.code or '',
            'currency': self.currency_id.symbol or '',
            'total': "{:,}".format(total) if total else '0',
            'lines': line or '',
        })

        return self.env.ref('report_form.action_statement_payment_pdf').report_action(self, data={
            'records': records,
        })

    def get_statement_receipt_report(self):
        records = []
        line = []
        total = 0

        if self.line_ids:
            for lines in self.line_ids:
                line.append({
                    'p_ref': lines.payment_ref or '',
                    'amount': "{:,}".format(lines.amount) if lines.amount else '0',
                })
                total += lines.amount

        records.append({
            'phone': self.company_id.phone or '',
            'mail': self.company_id.email or '',
            'website': self.company_id.website or '',
            'street': self.company_id.street or '',
            'street1': self.company_id.street2 or '',
            'country': self.company_id.country_id.name if self.company_id.country_id else '',
            'city': self.company_id.city or '',
            'state': self.company_id.state_id.name if self.company_id.state_id else '',
            'ref': self.name or '',
            'date': self.date or '',
            'code': self.code or '',
            'currency': self.currency_id.symbol or '',
            'total': "{:,}".format(total) if total else '0',
            'lines': line or '',
        })

        return self.env.ref('report_form.action_statement_receipt_report_pdf').report_action(self, data={
            'records': records,
        })

    def get_statement_advance_report(self):
        records = []
        line = []
        total = 0

        if self.line_ids:
            for lines in self.line_ids:
                line.append({
                    'p_ref': lines.payment_ref or '',
                    'amount': "{:,}".format(lines.amount) if lines.amount else '0',
                })
                total += lines.amount

        records.append({
            'phone': self.company_id.phone or '',
            'mail': self.company_id.email or '',
            'website': self.company_id.website or '',
            'street': self.company_id.street or '',
            'street1': self.company_id.street2 or '',
            'country': self.company_id.country_id.name if self.company_id.country_id else '',
            'city': self.company_id.city or '',
            'state': self.company_id.state_id.name if self.company_id.state_id else '',
            'ref': self.name or '',
            'date': self.date or '',
            'code': self.code or '',
            'currency': self.currency_id.symbol or '',
            'total': "{:,}".format(total) if total else '0',
            'lines': line or '',
        })

        return self.env.ref('report_form.action_statement_advance_report_pdf').report_action(self, data={
            'records': records,
        })
