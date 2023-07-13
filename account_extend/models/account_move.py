from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
from odoo.http import request


class AccountMoveExtend(models.Model):
    _inherit = 'account.move'

    paid_amount = fields.Float('Paid Amount', compute='_compute_paid_amount')

    def _compute_paid_amount(self):
        self.paid_amount = 0.0
        for rec in self:
            if rec.state == 'posted':
                rec.paid_amount += rec.amount_total - rec.amount_residual

    @api.onchange('company_id', 'partner_id', 'move_type')
    def onchange_company_id(self):
        for rec in self:
            if rec.move_type in ['in_invoice', 'in_refund', 'in_receipt']:
                suppliers = self.env['res.partner'].search([('supplier', '=', True)])
                return {'domain': {'partner_id': [('id', 'in', suppliers.ids)]}}
            else:
                customers = self.env['res.partner'].search([('customer', '=', True)])
                return {'domain': {'partner_id': [('id', 'in', customers.ids)]}}

    """FOR CUSTOMER """

    def check_access_invoices(self):
        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])
            if employee_id and employee_id.user_id.is_concurrent_user:
                allow_journals = employee_id.journal_ids.ids
                if allow_journals:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': ('Invoices'),
                        'res_model': 'account.move',
                        'view_mode': 'tree,kanban,form',
                        'domain': [('journal_id', 'in', allow_journals), ('move_type', '=', 'out_invoice')],
                        'context': {'default_move_type': 'out_invoice'},
                    }
                else:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': ('Invoices'),
                        'res_model': 'account.move',
                        'view_mode': 'tree,kanban,form',
                        'domain': [('journal_id', 'in', []), ('move_type', '=', 'out_invoice')],
                        'context': {'default_move_type': 'out_invoice'},
                    }
            else:
                allow_journals = self.env['account.journal'].search([])
                return {
                    'type': 'ir.actions.act_window',
                    'name': ('Invoices'),
                    'res_model': 'account.move',
                    'view_mode': 'tree,kanban,form',
                    'domain': [('journal_id', 'in', allow_journals), ('move_type', '=', 'out_invoice')],
                    'context': {'default_move_type': 'out_invoice'},
                }

    def check_access_credit_notes(self):
        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])
            if employee_id and employee_id.user_id.is_concurrent_user:
                allow_journals = employee_id.journal_ids.ids
                if allow_journals:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': ('Credit Notes'),
                        'res_model': 'account.move',
                        'view_mode': 'tree,kanban,form',
                        'domain': [('journal_id', 'in', allow_journals), ('move_type', '=', 'out_refund')],
                        'context': {'default_move_type': 'out_refund'},
                    }
                else:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': ('Credit Notes'),
                        'res_model': 'account.move',
                        'view_mode': 'tree,kanban,form',
                        'domain': [('journal_id', 'in', []), ('move_type', '=', 'out_refund')],
                        'context': {'default_move_type': 'out_refund'},
                    }
            else:
                allow_journals = self.env['account.journal'].search([])
                return {
                    'type': 'ir.actions.act_window',
                    'name': ('Credit Notes'),
                    'res_model': 'account.move',
                    'view_mode': 'tree,kanban,form',
                    'domain': [('journal_id', 'in', allow_journals), ('move_type', '=', 'out_refund')],
                    'context': {'default_move_type': 'out_refund'},
                }

    """FOR VENDOR"""

    def check_access_bills(self):
        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])
            if employee_id and employee_id.user_id.is_concurrent_user:
                allow_journals = employee_id.journal_ids.ids
                if allow_journals:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': ('Bills'),
                        'res_model': 'account.move',
                        'view_mode': 'tree,kanban,form',
                        'domain': [('journal_id', 'in', allow_journals), ('move_type', '=', 'in_invoice')],
                        'context': {'default_move_type': 'in_invoice'},
                    }
                else:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': ('Bills'),
                        'res_model': 'account.move',
                        'view_mode': 'tree,kanban,form',
                        'domain': [('journal_id', 'in', []), ('move_type', '=', 'in_invoice')],
                        'context': {'default_move_type': 'in_invoice'},
                    }
            else:
                allow_journals = self.env['account.journal'].search([])
                return {
                    'type': 'ir.actions.act_window',
                    'name': ('Bills'),
                    'res_model': 'account.move',
                    'view_mode': 'tree,kanban,form',
                    'domain': [('journal_id', 'in', allow_journals), ('move_type', '=', 'in_invoice')],
                    'context': {'default_move_type': 'in_invoice'},
                }

    def check_access_refunds(self):
        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])
            if employee_id and employee_id.user_id.is_concurrent_user:
                allow_journals = employee_id.journal_ids.ids
                if allow_journals:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': ('Refunds'),
                        'res_model': 'account.move',
                        'view_mode': 'tree,kanban,form',
                        'domain': [('journal_id', 'in', allow_journals), ('move_type', '=', 'in_refund')],
                        'context': {'default_move_type': 'in_refund'},
                    }
                else:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': ('Refunds'),
                        'res_model': 'account.move',
                        'view_mode': 'tree,kanban,form',
                        'domain': [('journal_id', 'in', []), ('move_type', '=', 'in_refund')],
                        'context': {'default_move_type': 'in_refund'},
                    }
            else:
                allow_journals = self.env['account.journal'].search([])
                return {
                    'type': 'ir.actions.act_window',
                    'name': ('Refunds'),
                    'res_model': 'account.move',
                    'view_mode': 'tree,kanban,form',
                    'domain': [('journal_id', 'in', allow_journals), ('move_type', '=', 'in_refund')],
                    'context': {'default_move_type': 'in_refund'},
                }


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def check_access_journal_items(self):
        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])
            if employee_id and employee_id.user_id.is_concurrent_user:
                allow_journals = employee_id.journal_ids.ids
                if allow_journals:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': ('Journal Items'),
                        'res_model': 'account.move.line',
                        'view_mode': 'tree,pivot,graph,kanban,form',
                        'domain': [('journal_id', 'in', allow_journals), ('display_type', 'not in', ('line_section', 'line_note')), ('parent_state', '!=', 'cancel')],
                        'context': {'journal_type':'general', 'search_default_posted':1},
                    }
                else:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': ('Journal Items'),
                        'res_model': 'account.move.line',
                        'view_mode': 'tree,pivot,graph,kanban,form',
                        'domain': [('journal_id', 'in', []), ('display_type', 'not in', ('line_section', 'line_note')), ('parent_state', '!=', 'cancel')],
                        'context': {'default_move_type': 'in_refund'},
                    }
            else:
                allow_journals = self.env['account.journal'].search([])
                return {
                    'type': 'ir.actions.act_window',
                    'name': ('Journal Items'),
                    'res_model': 'account.move.line',
                    'view_mode': 'tree,pivot,graph,kanban,form',
                    'domain': [('journal_id', 'in', allow_journals), ('display_type', 'not in', ('line_section', 'line_note')), ('parent_state', '!=', 'cancel')],
                    'context': {'default_move_type': 'in_refund'},
                }


