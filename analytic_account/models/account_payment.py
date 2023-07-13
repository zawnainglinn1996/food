from odoo import api, models, fields, _ 


class AccountPayment(models.Model):

    _inherit = 'account.payment'

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    allow_analytic_account_ids = fields.Many2many('account.analytic.account', string='Analytic Accounts',
                                                  related='login_employee_id.allow_analytic_account_id')
    def action_post(self):
        res = super(AccountPayment, self).action_post()
        for payment in self:
            payment.move_id.write({'analytic_account_id': payment.analytic_account_id.id})
        return res
