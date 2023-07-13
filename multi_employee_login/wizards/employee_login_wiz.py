from odoo import models,fields,api,http,_
from odoo.http import request
from odoo.exceptions import AccessError, MissingError, ValidationError, UserError


class Employee_login(models.TransientModel):
    _name = 'hr.employee.login'
    _description= 'Hr Employee Login'

    user_id = fields.Many2one(
        'res.users',
        'User',
        required=True,
        default=lambda self: self.env.user
    )
    employee_id = fields.Many2one(
        'hr.employee',
        "Employee:",
        required=True
    )
    employee_pin = fields.Char(
        "PIN Code:",
        required = True
    )
    alert_message = fields.Char(
        ""
    )

    def action_login(self):
        if self.employee_id.pin == self.employee_pin:
            request.session.emp_id = self.employee_id.id
            self.alert_message = ""
            return {
                'type': 'ir.actions.act_url',
                'target': 'self',
                'url': '/web',
            }
        else:
            raise ValidationError(_("Please Try Again. Invalid Pin !!"))
            # self.alert_message= "Please Try Again. Invalid Pin !!"
            # return {
            #     'name': 'Select your Employee name!',
            #     'type': 'ir.actions.act_window',
            #     'view_type': 'form',
            #     'view_mode': 'form',
            #     'res_model': 'hr.employee.login',
            #     'res_id': self.id,
            #     'target': 'new',
            # }

