from odoo import models, fields, api, _
from odoo.http import request
from odoo.fields import Date
from odoo.exceptions import UserError, ValidationError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

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
        res = super(PurchaseOrder, self).create(vals)
        message = (f"Create By: ==> {res.login_employee_id.name}")
        res.message_post(body=message)
        return res

    def action_confirm(self):
        res = super(PurchaseOrder, self).action_confirm()
        message = (f"Confrim By: ==> {self.login_employee_id.name}")
        self.message_post(body=message)
        return res

    def action_verified(self):
        res = super(PurchaseOrder, self).action_verified()
        message = (f"Verified By: ==> {self.login_employee_id.name}")
        self.message_post(body=message)
        return res

    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        message = (f"Approved By: ==> {self.login_employee_id.name}")
        self.message_post(body=message)
        return res

    @api.model
    def _prepare_picking(self):
        """
        Inherited for adding relation with ICT if created by it.
        @author: Maulik Barad on Date 16-Oct-2019.
        @return: Dictionary for creating picking.
        """
        vals = super(PurchaseOrder, self)._prepare_picking()

        vals.update({
            'login_employee_id': self.login_employee_id.id
        })
        return vals

    def action_view_invoice(self, invoices=False):
        """
        Inherited for adding relation with ICT if created by it.
        @author: Maulik Barad on Date 16-Oct-2019.
        @return: Action for displaying vendor bill for purchase order.
        """
        action = super(PurchaseOrder, self).action_view_invoice()
        message = (f"Create Bill By: ==> {self.login_employee_id.name}")
        self.message_post(body=message)
        if self.env.context.get('create_bill', False):
            ctx = eval(action['context'])
            action['context'] = ctx

            action['context']['default_login_employee_id'] = self.login_employee_id.id
        return action

    @api.onchange('login_employee_id')
    def onchange_employee(self):
        if request.session.emp_id:
            employee_id = self.env['hr.employee'].browse(int(request.session.emp_id))
        else:
            employee_id = self.env.user.employee_id
        self.prepare_by_sign = employee_id.user_signature
        self.prepare_by_date = Date.today()
        self.prepare_by_name = employee_id.id


class StockRequestion(models.Model):
    _inherit = 'stock.requestion'

    @api.model
    def create(self, vals):
        res = super(StockRequestion, self).create(vals)
        message = (f"Create By: ==> {res.login_employee_id.name}")
        res.message_post(body=message)
        return res

    def action_draft(self):
        res = super(StockRequestion, self).action_draft()
        message = (f"Draft By: ==> {self.login_employee_id.name}")
        self.message_post(body=message)
        return res

    def action_submit(self):
        res = super(StockRequestion, self).action_submit()
        message = (f"Submit By: ==> {self.login_employee_id.name}")
        self.message_post(body=message)
        return res

    def action_cancel(self):
        res = super(StockRequestion, self).action_cancel()
        message = (f"Cancel By: ==> {self.login_employee_id.name}")
        self.message_post(body=message)
        return res

    def action_verified(self):
        res = super(StockRequestion, self).action_verified()
        message = (f"Verified By: ==> {self.login_employee_id.name}")
        self.message_post(body=message)
        return res

    def action_approved(self):
        res = super(StockRequestion, self).action_approved()
        message = (f"Approved By: ==> {self.login_employee_id.name}")
        self.message_post(body=message)
        return res

    def action_confirm(self):
        res = super(StockRequestion, self).action_confirm()
        message = (f"Confirm By: ==> {self.login_employee_id.name}")
        self.message_post(body=message)
        return res



class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

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

    @api.model
    def create(self, vals):
        res = super(PurchaseRequisition, self).create(vals)
        message = (f"Create By: ==> {res.login_employee_id.name}")
        res.message_post(body=message)
        return res

    def action_in_progress(self):
        res = super(PurchaseRequisition, self).action_in_progress()
        message = (f"Progress By: ==> {self.login_employee_id.name}")
        self.message_post(body=message)
        return res

    def action_open(self):
        res = super(PurchaseRequisition, self).action_open()
        message = (f"Open By: ==> {self.login_employee_id.name}")
        self.message_post(body=message)
        return res

    def action_done(self):
        res = super(PurchaseRequisition, self).action_done()
        message = (f"Done By: ==> {self.login_employee_id.name}")
        self.message_post(body=message)
        return res



