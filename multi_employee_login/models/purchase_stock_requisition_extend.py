from odoo import models, fields, api, _
from odoo.http import request


class PurchaseStockRequisition(models.Model):
    _inherit = 'purchase.stock.requisition'

    def _get_current_employee(self):
        if request.session.emp_id:
            return int(request.session.emp_id)
        elif not self.env.user.is_concurrent_user:
            return int(self.env.user.employee_id.id)
        else:
            return False

    login_employee_id = fields.Many2one(
        'hr.employee',
        string="Employee ", tracking=True,
        default=lambda self: self._get_current_employee()
    )

    @api.model
    def create(self, vals):
        res = super(PurchaseStockRequisition, self).create(vals)
        message = (f"Create By: ==> {res.login_employee_id.name}")
        res.message_post(body=message)
        return res

    def action_confirm(self):
        res = super(PurchaseStockRequisition, self).action_confirm()
        message = (f"Confirm By: ==> {self.login_employee_id.name}")
        self.message_post(body=message)
        return res

    def action_verified(self):
        res = super(PurchaseStockRequisition, self).action_verified()
        message = (f"Verified By: ==> {self.login_employee_id.name}")
        self.message_post(body=message)
        return res

    def action_approved(self):
        res = super(PurchaseStockRequisition, self).action_approved()
        message = (f"Approved By: ==> {self.login_employee_id.name}")
        self.message_post(body=message)
        return res

    def action_checked(self):
        res = super(PurchaseStockRequisition, self).action_checked()
        message = (f"Checked By: ==> {self.login_employee_id.name}")
        self.message_post(body=message)
        return res

    def action_cancel(self):
        res = super(PurchaseStockRequisition, self).action_cancel()
        message = (f"Cancel By: ==> {self.login_employee_id.name}")
        self.message_post(body=message)
        return res



class PurchaseRequisitionLine(models.Model):
    _inherit = 'purchase.requisitions.line'

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



