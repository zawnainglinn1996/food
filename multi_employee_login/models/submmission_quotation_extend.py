from odoo import models, fields, api, _
from odoo.http import request


class SubmissionQuotation(models.Model):
    _inherit = 'submission.quotation'

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
        res = super(SubmissionQuotation, self).create(vals)
        message = (f"Create By: ==> {res.login_employee_id.name}")
        res.message_post(body=message)
        return res

    def action_submit(self):
        res = super(SubmissionQuotation, self).action_submit()
        message = (f"Submit By: ==> {self.login_employee_id.name}")
        self.message_post(body=message)
        return res

    def action_confirm(self):
        res = super(SubmissionQuotation, self).action_confirm()
        message = (f"Confirm By: ==> {self.login_employee_id.name}")
        self.message_post(body=message)
        return res

    def action_checked(self):
        res = super(SubmissionQuotation, self).action_checked()
        message = (f"Checked By: ==> {self.login_employee_id.name}")
        self.message_post(body=message)
        return res

    def action_approved(self):
        res = super(SubmissionQuotation, self).action_approved()
        message = (f"Approved By: ==> {self.login_employee_id.name}")
        self.message_post(body=message)
        return res

    def action_cancel(self):
        res = super(SubmissionQuotation, self).action_cancel()
        message = (f"Cancel By: ==> {self.login_employee_id.name}")
        self.message_post(body=message)
        return res
