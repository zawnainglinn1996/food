from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.http import request


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')

    @api.onchange('journal_id')
    def onchange_analytic_account(self):
        journal_ids = False
        journal_list = []
        for rec in self:
            if request.session.emp_id:
                data = int(request.session.emp_id)
                employee_id = self.env['hr.employee'].search([('id', '=', data)])
                if employee_id:
                    journal_ids = employee_id.journal_ids

            if journal_ids:
                for journal in journal_ids:
                    if journal.type == 'cash' or journal.type == 'bank':
                        journal_list.append(journal.id)
                return {'domain': {'journal_id': [('id', 'in', journal_list)]}}

    def _create_payments(self):
        payments = super(AccountPaymentRegister, self)._create_payments()
        for payment in payments:
            payment.write({'analytic_account_id': self.analytic_account_id.id})
        return payments
