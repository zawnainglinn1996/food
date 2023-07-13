from odoo import models, fields, api
from odoo.http import request


class Stock_Scrap(models.Model):

    _inherit = 'stock.scrap'

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

    @api.model
    def create(self, vals):
        res = super(Stock_Scrap, self).create(vals)
        message = (f"Create By: ==> {res.login_employee_id.name}")
        res.message_post(body=message)
        return res

    def action_validate(self):
        res = super(Stock_Scrap, self).action_validate()
        message = (f"Validate By: ==> {self.login_employee_id.name}")
        self.message_post(body=message)
        return res