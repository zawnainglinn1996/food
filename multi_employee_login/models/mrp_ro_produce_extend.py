from odoo import models, fields, api, _
from odoo.http import request
from odoo.exceptions import UserError

class MrpProduce(models.Model):
    _inherit = 'mrp.produce'

    login_employee_id = fields.Many2one(
        'hr.employee',
        string="Employee", tracking=True,
        default=lambda self: self._get_current_employee()
    )

    confirm_by_sign = fields.Binary(string='Confirm Sign', help='For Confirm By Sign')
    confirm_by_emp_id = fields.Many2one('hr.employee', string='Confirm Name', help='For Confirm By Name')
    confirm_by_position = fields.Char(string='Confirm Position', help='For Confirm By Position')

    is_confirmed = fields.Boolean('Confirmed',default=False)

    def _get_current_employee(self):
        if request.session.emp_id:
            return int(request.session.emp_id)
        elif not self.env.user.is_concurrent_user:
            return int(self.env.user.employee_id.id)
        else:
            return False

    def button_confirm(self):
        res = super(MrpProduce, self).button_confirm()

        if not self.is_confirmed:
            self.is_confirmed=True
        else:
            raise UserError(
                "This Record is Already Confirm By %s  .Please Refresh Your Browser Thanks" % self.confirm_by_emp_id.name )
        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])

            self.confirm_by_sign = employee_id.user_signature
            self.confirm_by_emp_id = employee_id.id
        else:
            self.confirm_by_sign = self.env.user.employee_id.user_signature
            self.confirm_by_emp_id = self.env.user.employee_id.id
        message = (f"MO PRODUCE CONFIRM By: ==> {self.confirm_by_emp_id.name}")
        self.message_post(body=message)
        return res
