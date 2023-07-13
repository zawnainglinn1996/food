from odoo import models,fields,api
from odoo.http import request

class Sale_order_(models.Model):
    _inherit = 'sale.order'

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

    def _prepare_invoice(self):
        self.ensure_one()
        values = super(Sale_order_, self)._prepare_invoice()
        values.update({
            'login_employee_id': self.login_employee_id.id
        })
        return values

    def action_confirm(self):
        res = super(Sale_order_, self).action_confirm()
        message = (f"Confirm By: ==> {self.login_employee_id.name}")
        self.message_post(body=message)
        return res

    def action_sale_requistion(self):
        res = super(Sale_order_, self).action_sale_requistion()
        message = (f"Sale Requisition By: ==> {self.login_employee_id.name}")
        self.message_post(body=message)
        return res

    def action_cancel(self):
        res=super(Sale_order_, self).action_cancel()
        message = (f"Cancel By: ==> {self.login_employee_id.name}")
        self.message_post(body=message)
        return res

    def _create_invoices(self, grouped=False, final=False, date=None):
        res = super(Sale_order_, self)._create_invoices(grouped, final, date)
        message = (f"Create Invoice By: ==> {self.login_employee_id.name}")
        self.message_post(body=message)
        return res

    @api.model
    def create(self, vals):
        res = super(Sale_order_, self).create(vals)
        message = (f"Create By: ==> {res.login_employee_id.name}")
        res.message_post(body=message)
        return res


class WholeSaleRequisition(models.Model):
    _inherit = 'whole.sale.requisition'

    @api.model
    def create(self, vals):
        res = super(WholeSaleRequisition, self).create(vals)
        message = (f"Create By: ==> {res.login_employee_id.name}")
        res.message_post(body=message)
        return res

    def action_confirm(self):
        res = super(WholeSaleRequisition, self).action_confirm()
        message = (f"Confirm By: ==> {self.login_employee_id.name}")
        self.message_post(body=message)
        return res

    def action_approved(self):
        res = super(WholeSaleRequisition, self).action_approved()
        message = (f"Approved By: ==> {self.login_employee_id.name}")
        self.message_post(body=message)
        return res

    def action_cancel(self):
        res = super(WholeSaleRequisition, self).action_cancel()
        message = (f"Cancel By: ==> {self.login_employee_id.name}")
        self.message_post(body=message)
        return res


