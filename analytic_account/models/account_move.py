from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round
from odoo.exceptions import ValidationError
from odoo.http import request


class AccountMove(models.Model):
    _inherit = 'account.move'

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    allow_analytic_account_ids = fields.Many2many('account.analytic.account', string='Analytic Accounts',
                                                  related='login_employee_id.allow_analytic_account_id')
    @api.model
    def _prepare_move_for_asset_depreciation(self, vals):
        missing_fields = set(
            ['asset_id', 'move_ref', 'amount', 'asset_remaining_value', 'asset_depreciated_value']) - set(vals)
        if missing_fields:
            raise UserError(_('Some fields are missing {}').format(', '.join(missing_fields)))
        asset = vals['asset_id']
        account_analytic_id = asset.account_analytic_id
        analytic_tag_ids = asset.analytic_tag_ids
        depreciation_date = vals.get('date', fields.Date.context_today(self))
        company_currency = asset.company_id.currency_id
        current_currency = asset.currency_id
        prec = company_currency.decimal_places
        amount = current_currency._convert(vals['amount'], company_currency, asset.company_id, depreciation_date)
        # Keep the partner on the original invoice if there is only one
        partner = asset.original_move_line_ids.mapped('partner_id')
        partner = partner[:1] if len(partner) <= 1 else self.env['res.partner']
        move_line_1 = {
            'name': asset.name,
            'partner_id': partner.id,
            'account_id': asset.account_depreciation_id.id,
            'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
            'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
            'analytic_account_id': account_analytic_id.id if asset.asset_type == 'sale' else False,
            'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if asset.asset_type == 'sale' else False,
            'currency_id': current_currency.id,
            'amount_currency': -vals['amount'],
        }
        move_line_2 = {
            'name': asset.name,
            'partner_id': partner.id,
            'account_id': asset.account_depreciation_expense_id.id,
            'credit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
            'debit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
            'analytic_account_id': account_analytic_id.id if asset.asset_type in ('purchase', 'expense') else False,
            'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if asset.asset_type in (
                'purchase', 'expense') else False,
            'currency_id': current_currency.id,
            'amount_currency': vals['amount'],
        }
        move_vals = {
            'ref': vals['move_ref'],
            'partner_id': partner.id,
            'analytic_account_id': asset.account_analytic_id.id,
            'date': depreciation_date,
            'journal_id': asset.journal_id.id,
            'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
            'asset_id': asset.id,
            'asset_remaining_value': vals['asset_remaining_value'],
            'asset_depreciated_value': vals['asset_depreciated_value'],
            'amount_total': amount,
            'name': '/',
            'asset_value_change': vals.get('asset_value_change', False),
            'move_type': 'entry',
            'currency_id': current_currency.id,
        }
        return move_vals

    """ DEFAULT JOURNAL AND DEFAULT JOURNAL ACCESS UNDER METHODS"""

    def action_register_payment(self):
        action = super(AccountMove, self).action_register_payment()

        context = action.get('context')
        context.update({'default_analytic_account_id': self.analytic_account_id.id})
        return action

    @api.model
    def default_get(self, fields_list):
        vals = super(AccountMove, self).default_get(fields_list)
        default_journal_id = False
        analytic_account_id = False
        move_type = vals.get('move_type')
        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])
            if employee_id:
                journal_id = employee_id.default_journal_id
                analytic_account_id = employee_id.def_analytic_account_id.id
                if move_type in ['in_invoice', 'in_refund', 'in_receipt']:
                    if journal_id.type != 'purchase':
                        allow_journals = employee_id.journal_ids
                        journals = allow_journals.filtered(lambda l:l.type=='purchase')
                        default_journal_id = journals[0]
                if move_type in ['out_invoice', 'out_refund', 'out_receipt']:
                    if journal_id.type != 'sale':
                        allow_journals = employee_id.journal_ids
                        journals = allow_journals.filtered(lambda l:l.type=='sale')
                        default_journal_id = journals[0]
        if default_journal_id:
            vals.update({'journal_id': default_journal_id})

        vals.update({'analytic_account_id': analytic_account_id})
        return vals



    @api.onchange('journal_id')
    def onchange_journal(self):

        journal_list = []
        for rec in self:
            if rec.move_type == 'entry':
                if request.session.emp_id:
                    data = int(request.session.emp_id)
                    employee_id = self.env['hr.employee'].search([('id', '=', data)])

                    if employee_id:
                        default_journal_id = employee_id.default_journal_id.id

                        if not default_journal_id:
                            raise ValidationError(
                                _("Default Journal ID is Missing in Employee - ( %s)!" % (self.login_employee_id.name)))
                        else:
                            return {'domain': {'journal_id': [('id', 'in', employee_id.journal_ids.ids)]}}
            if rec.move_type in ['in_invoice', 'in_refund', 'in_receipt']:
                if request.session.emp_id:
                    data = int(request.session.emp_id)
                    employee_id = self.env['hr.employee'].search([('id', '=', data)])

                    if employee_id:
                        journal_ids = employee_id.journal_ids
                        for journal in journal_ids:
                            if journal.type == 'purchase':
                                journal_list.append(journal.id)
                        return {'domain': {'journal_id': [('id', 'in', journal_list)]}}
            if rec.move_type in ['out_invoice', 'out_refund', 'out_receipt']:
                if request.session.emp_id:
                    data = int(request.session.emp_id)
                    employee_id = self.env['hr.employee'].search([('id', '=', data)])

                    if employee_id:
                        journal_ids = employee_id.journal_ids
                        for journal in journal_ids:
                            if journal.type == 'sale':
                                journal_list.append(journal.id)
                        return {'domain': {'journal_id': [('id', 'in', journal_list)]}}


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    analytic_account_id = fields.Many2one(compute='_compute_analytic_account')

    @api.depends('product_id', 'account_id', 'partner_id', 'date_maturity', 'move_id.analytic_account_id')
    def _compute_analytic_account(self):
        for rec in self:
            rec.analytic_account_id = False
            move = rec.move_id
            analytic_account = move.analytic_account_id
            if analytic_account:
                rec.analytic_account_id = analytic_account.id
