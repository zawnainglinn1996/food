from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import float_compare
from odoo.addons import decimal_precision as dp
from odoo.http import request
import logging

_logger = logging.getLogger('Invoice-Manual-Currency-Inherit')


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')

    def button_post(self):
        data = super(AccountBankStatement, self).button_post()
        for rec in self.line_ids:
            rec.move_id.write({'analytic_account_id': rec.analytic_account_id})
        return data


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account',
                                          related=False)

    @api.model
    def default_get(self, fields_list):
        vals = super(AccountBankStatementLine, self).default_get(fields_list)
        default_analytic_account_id = False

        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])
            if employee_id:
                analytic_account_id = employee_id.def_analytic_account_id.id
                default_analytic_account_id = analytic_account_id
        if default_analytic_account_id:
            vals.update({'analytic_account_id': default_analytic_account_id})
        return vals

    @api.onchange('analytic_account_id')
    def onchange_analytic_account(self):
        for rec in self:
            if request.session.emp_id:
                data = int(request.session.emp_id)
                employee_id = self.env['hr.employee'].search([('id', '=', data)])

                if employee_id:
                    return {
                        'domain': {'analytic_account_id': [('id', 'in', employee_id.allow_analytic_account_id.ids)]}}

    def _prepare_reconciliation_move(self, move_ref):

        ref = move_ref or ''
        if self.ref:
            ref = move_ref + ' - ' + self.ref if move_ref else self.ref
        data = {
            'type': 'entry',
            'journal_id': self.statement_id.journal_id.id,
            'currency_id': self.statement_id.currency_id.id,
            'analytic_account_id': self.statement_id.analytic_account_id.id,
            'date': self.statement_id.accounting_date or self.date,
            'partner_id': self.partner_id.id,
            'ref': ref,
        }
        if self.move_name:
            data.update(name=self.move_name)
        return data
