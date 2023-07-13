from odoo import models,api,fields
from odoo.http import request

class Res_users_concurrent(models.Model):
    _inherit = 'res.users'

    is_concurrent_user = fields.Boolean(
        "Concurrent User",
        default=False
    )

    @api.model
    def get_employee_login(self):
        return {
            'is_concurrent_user': request.env.user.is_concurrent_user,
            'emp_id': request.session.emp_id,
            'action_id' : request.env.ref('multi_employee_login.action_hr_employee_login').id
        }