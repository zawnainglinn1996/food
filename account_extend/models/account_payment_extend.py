from odoo import models, fields, api, _
from odoo.http import request
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.onchange('company_id', 'partner_id', 'payment_type')
    def onchange_company_id(self):
        for rec in self:
            if rec.payment_type == 'outbound':
                suppliers = self.env['res.partner'].search([('supplier', '=', True)])
                return {'domain': {'partner_id': [('id', 'in', suppliers.ids)]}}
            else:
                customers = self.env['res.partner'].search([('customer', '=', True)])
                return {'domain': {'partner_id': [('id', 'in', customers.ids)]}}

    def check_access_payments(self):
        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])
            if employee_id and employee_id.user_id.is_concurrent_user:
                allow_journals = employee_id.journal_ids.ids
                if allow_journals:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': ('Payments'),
                        'res_model': 'account.payment',
                        'view_mode': 'tree,kanban,form,graph',
                        'domain': [('journal_id', 'in', allow_journals), ('move_type', '=', 'out_receipt')],
                        'context': {'default_move_type': 'out_receipt'},
                    }
                else:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': ('Payments'),
                        'res_model': 'account.payment',
                        'view_mode': 'tree,kanban,form,graph',
                        'domain': [('journal_id', 'in', []), ('move_type', '=', 'out_receipt')],
                        'context': {'default_move_type': 'out_receipt'},
                    }
            else:
                allow_journals = self.env['account.journal'].search([])
                return {
                    'type': 'ir.actions.act_window',
                    'name': ('Payments'),
                    'res_model': 'account.payment',
                    'view_mode': 'tree,kanban,form,graph',
                    'domain': [('journal_id', 'in', allow_journals), ('move_type', '=', 'out_receipt')],
                    'context': {'default_move_type': 'out_receipt'},
                }

    def check_access_vendor_payments(self):
        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])
            if employee_id and employee_id.user_id.is_concurrent_user:
                allow_journals = employee_id.journal_ids.ids
                if allow_journals:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': ('Payments'),
                        'res_model': 'account.payment',
                        'view_mode': 'tree,kanban,form,graph',
                        'domain': [('journal_id', 'in', allow_journals), ('move_type', '=', 'in_receipt')],
                        'context': {'default_move_type': 'in_receipt'},
                    }
                else:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': ('Payments'),
                        'res_model': 'account.payment',
                        'view_mode': 'tree,kanban,form,graph',
                        'domain': [('journal_id', 'in', []), ('move_type', '=', 'in_receipt')],
                        'context': {'default_move_type': 'in_receipt'},
                    }
            else:
                allow_journals = self.env['account.journal'].search([])
                return {
                    'type': 'ir.actions.act_window',
                    'name': ('Payments'),
                    'res_model': 'account.payment',
                    'view_mode': 'tree,kanban,form,graph',
                    'domain': [('journal_id', 'in', allow_journals), ('move_type', '=', 'in_receipt')],
                    'context': {'default_move_type': 'in_receipt'},
                }

    @api.model
    def default_get(self, fields_list):
        vals = super(AccountPayment, self).default_get(fields_list)
        default_journal_id = False
        analytic_account_id = False
        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])
            if employee_id:
                analytic_account_id = employee_id.def_analytic_account_id.id
                journal_ids = employee_id.journal_ids.filtered(lambda l: l.type == 'bank' or l.type == 'cash')
                if journal_ids:
                    default_journal_id = journal_ids[0]
        if default_journal_id:
            vals.update({'journal_id': default_journal_id})
        vals.update({'analytic_account_id': analytic_account_id})
        return vals

    @api.onchange('journal_id')
    def onchange_journal(self):
        for rec in self:
            if request.session.emp_id:
                data = int(request.session.emp_id)
                employee_id = self.env['hr.employee'].search([('id', '=', data)])

                if employee_id:
                    journal_ids = employee_id.journal_ids.filtered(lambda l: l.type == 'bank' or l.type == 'cash')
                    return {'domain': {'journal_id': [('id', 'in', journal_ids.ids)]}}
