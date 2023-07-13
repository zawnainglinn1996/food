from odoo import models, fields, api, _
from odoo.http import request


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    def check_access_journal(self):
        view_form = self.env.ref('account.account_journal_dashboard_kanban_view')
        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])
            if employee_id and employee_id.user_id.is_concurrent_user:
                allow_journals = employee_id.journal_ids.ids

                if allow_journals:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': ('Accounting Dashboard'),
                        'res_model': 'account.journal',
                        'view_id': view_form.id,
                        'views': [(view_form.id, 'kanban'), (False, 'form')],
                        'view_mode': 'kanban,form',
                        'domain': [('id', 'in', allow_journals)],
                        'context': {'search_default_dashboard':1},
                    }
                else:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': ('Accounting Dashboard'),
                        'res_model': 'account.journal',
                        'view_id': view_form.id,
                        'views': [(view_form.id, 'kanban'), (False, 'form')],
                        'view_mode': 'kanban,form',
                        'domain': [('id', 'in', [])],
                        'context': {'search_default_dashboard':1},
                    }
            else:
                allow_journals = self.env['account.journal'].search([])
                return {
                    'type': 'ir.actions.act_window',
                    'name': ('Accounting Dashboard'),
                    'res_model': 'account.journal',
                    'view_id': view_form.id,
                    'views': [(view_form.id, 'kanban'), (False, 'form')],
                    'view_mode': 'kanban,form',
                    'domain': [('id', 'in', allow_journals)],
                    'context': {'search_default_dashboard':1},
                }
