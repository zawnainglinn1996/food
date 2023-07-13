from odoo import models, fields, api
from odoo.http import request


class HrExpense(models.Model):
    _inherit = "hr.expense"

    def _get_current_employee(self):
        if request.session.emp_id:
            return int(request.session.emp_id)
        elif not self.env.user.is_concurrent_user:
            return int(self.env.user.employee_id.id)
        else:
            return False

    login_employee_id = fields.Many2one('hr.employee', string="Employee Login", tracking=True,
                                        default=lambda self: self._get_current_employee())

    @api.onchange('company_id')
    def _onchange_expense_company_id(self):
        if self.env.user.is_concurrent_user:
            self.employee_id = self.login_employee_id.id
        else:
            self.employee_id = self.env['hr.employee'].search(
                [('user_id', '=', self.env.uid), ('company_id', '=', self.company_id.id)])


class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    def _get_current_employee(self):
        if request.session.emp_id:
            return int(request.session.emp_id)
        elif not self.env.user.is_concurrent_user:
            return int(self.env.user.employee_id.id)
        else:
            return False

    login_employee_id = fields.Many2one('hr.employee', string="Employee Login", default=lambda self: self._get_current_employee())


