from odoo import models, fields, api
from odoo.http import request


class MRP(models.Model):

    _inherit = 'mrp.production'

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
    # user_signature = fields.Binary(string="User Signature",related="login_employee_id.user_signature")
