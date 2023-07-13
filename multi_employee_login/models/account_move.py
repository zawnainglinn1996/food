from odoo import models, fields, api
from odoo.http import request


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_current_employee(self):
        if request.session.emp_id:
            return int(request.session.emp_id)
        elif not self.env.user.is_concurrent_user:
            return int(self.env.user.employee_id.id)
        else:
            return False

    login_employee_id = fields.Many2one(
        'hr.employee',
        string="Employee",
        default=lambda self: self._get_current_employee()
    )


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def _get_current_employee(self):
        if request.session.emp_id:
            return int(request.session.emp_id)
        elif not self.env.user.is_concurrent_user:
            return int(self.env.user.employee_id.id)
        else:
            return False

    login_employee_id = fields.Many2one(
        'hr.employee',
        string="Employee",
        default=lambda self: self._get_current_employee()
    )
