from odoo import models,fields,api,_


class HrEmployeePrivate(models.Model):
    _inherit = 'hr.employee'

    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse', check_company=True)
    user_signature = fields.Binary(string="User Signature")

    def_analytic_account_id = fields.Many2one('account.analytic.account', 'Default Analytic Account')
    allow_analytic_account_id = fields.Many2many('account.analytic.account', 'account_analytic_account_hr_employee_rel', 'hr_employee_id', 'account_analytic_account_id', string='Allow Analytic Account')

    location_id = fields.Many2one('stock.location', string='Location')

    journal_ids = fields.Many2many('account.journal', 'account_journal_hr_employee_rel', 'hr_employee_id', 'account_journal_id', string="Allow Journal")
    default_journal_id = fields.Many2one('account.journal', string="Default Journal")

