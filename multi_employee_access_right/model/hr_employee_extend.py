from odoo import models, fields, api, _


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    is_submit_access = fields.Boolean(string='Access Submit Button', default=False)
    is_confirm_access = fields.Boolean(string='Access Confirm Button', default=False)
    is_check_access = fields.Boolean(string='Access Check Button', default=False)
    is_approve_access = fields.Boolean(string='Access Approve Button', default=False)
    is_cancel_access = fields.Boolean(string='Access Cancel Button', default=False)

    is_submit_stock_req = fields.Boolean(string='Submit Button ', default=False)
    is_verified_stock_req = fields.Boolean(string='Verified Button ', default=False)
    is_approved_stock_req = fields.Boolean(string='Approved Button ', default=False)
    is_confirm_stock_req = fields.Boolean(string='Confirm Button ', default=False)
    is_cancel_stock_req = fields.Boolean(string='Cancel Button', default=False)

    is_sale_req_confirm = fields.Boolean(string='Confirm Button ', default=False)
    is_sale_req_approve = fields.Boolean(string='Approve Button ', default=False)
    is_sale_req_cancel = fields.Boolean(string='Cancel Button ', default=False)

    is_purchase_req_confirm = fields.Boolean(string='Confirm Button ', default=False)
    is_purchase_req_verified = fields.Boolean(string='Verified Button ', default=False)
    is_purchase_req_checked = fields.Boolean(string='Checked Button ', default=False)
    is_purchase_req_approved = fields.Boolean(string='Approved Button ', default=False)
    is_purchase_req_cancel = fields.Boolean(string='Cancel Button ', default=False)

    is_po_confirm = fields.Boolean(string='Confirm Button ', default=False)
    is_po_verified = fields.Boolean(string='Verified Button ', default=False)
    is_po_approved = fields.Boolean(string='Approved Button ', default=False)
    is_po_cancel = fields.Boolean(string='Cancel Button ', default=False)

    is_so_cancel = fields.Boolean(string='Sale Cancel Button', default=False)
    is_so_verify = fields.Boolean(string='Sale Verify Button', default=False)
    is_so_approve = fields.Boolean(string='Sale Approve Button',default=False)
