from odoo import api, models, fields, _ 
from odoo.http import request

class StockScrap(models.Model):

    _inherit = 'stock.scrap'

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    allow_analytic_account_ids = fields.Many2many('account.analytic.account', string='Analytic Accounts',
                                                  related='login_employee_id.allow_analytic_account_id')

    def do_scrap(self):
        res = super(StockScrap, self).do_scrap()
        if not self.analytic_account_id:
            return res
        account_moves = self.env['account.move'].search([('stock_move_id.id', '=', self.move_id.id)])
        for account_move in account_moves:
            account_move.analytic_account_id = self.analytic_account_id.id
        return res

    @api.model
    def default_get(self, fields_list):
        vals = super(StockScrap, self).default_get(fields_list)
        default_analytic_account_id = False
        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])
            if employee_id:
                analytic_id = employee_id.def_analytic_account_id.id
                if analytic_id:
                    default_analytic_account_id = analytic_id
        if default_analytic_account_id:
            vals.update({'analytic_account_id': default_analytic_account_id})
        return vals

    @api.onchange('analytic_account_id')
    def onchange_login_employee(self):
        for rec in self:
            if request.session.emp_id:
                data = int(request.session.emp_id)
                employee_id = self.env['hr.employee'].search([('id', '=', data)])

                if employee_id:
                    analytic_ids = employee_id.allow_analytic_account_id.ids
                    return {'domain': {'analytic_account_id': [('id', 'in', analytic_ids)]}}
            else:
                return {'domain': {'analytic_account_id': []}}
