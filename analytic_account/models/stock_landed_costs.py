from odoo import api, models, fields, _
from odoo.http import request


class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')

    def _get_current_employee(self):
        if request.session.emp_id:
            return int(request.session.emp_id)
        elif not self.env.user.is_concurrent_user:
            return int(self.env.user.employee_id.id)
        else:
            return False

    login_employee_id = fields.Many2one(
        'hr.employee',
        string="Employee", tracking=True,
        default=lambda self: self._get_current_employee()
    )

    allow_analytic_account_ids = fields.Many2many('account.analytic.account', string='Analytic Accounts',
                                                  related='login_employee_id.allow_analytic_account_id')

    def button_validate(self):
        res = super(StockLandedCost, self).button_validate()
        if not self.analytic_account_id or not self.account_move_id:
            return res
        self.account_move_id.analytic_account_id = self.analytic_account_id.id
        return res

    @api.model
    def default_get(self, fields_list):
        vals = super(StockLandedCost, self).default_get(fields_list)
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

