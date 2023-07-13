from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AssignAnalyticAccount(models.Model):
    _name = 'assign.analytic.account'
    _description = 'Assign Analytic Account to Journal'

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', required=True)

    def analytic_account_apply(self):
        selected_lines = self._context.get('active_ids')
        move_lines = self.env['account.move.line'].browse(selected_lines)

        for line in move_lines:
            line.write({'analytic_account_id': self.analytic_account_id})
