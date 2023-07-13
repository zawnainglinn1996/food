from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Date
from itertools import groupby
from odoo.http import request


class PurchaseStockRequisition(models.Model):
    _name = 'purchase.stock.requisition'
    _description = 'Purchase Requisition'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'reference_code'
    _order = 'id desc'

    request_date = fields.Date(string='Request Date', default=fields.Date.context_today)
    reference_code = fields.Char(string='Reference')
    employee_id = fields.Many2one('hr.employee', string='Employee', help='For Req By Name')
    department_id = fields.Many2one('hr.department', string='Department')
    product_family_id = fields.Many2one('product.family', string='Product Family')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company,
                                 required=True)
    user_id = fields.Many2one('res.users', string='To Approve')
    state = fields.Selection(
        [('draft', 'Draft'),
         ('requested', 'Requested'),
         ('verified', 'Verified'),
         ('checked', 'Checked'),
         ('approved', 'Approved'),
         ('cancel', 'Canceled')], string='State', default='draft', tracking=1)
    purchase_requisition_line = fields.One2many('purchase.requisitions.line', 'purchase_requisitions_id',
                                                string='Requisition Line', copy=True)

    req_by_sign = fields.Binary(string='Request Sign', help='For Req By Sign')
    req_by_name = fields.Many2one('hr.employee', string='Reuest Name', help='For Req By Name')
    req_by_date = fields.Date(string='Req By Date', help='For Req By Position', default=fields.Date.context_today)

    check_by_sign = fields.Binary(string='Check By Sign', help='for approved by sign')
    check_by_name = fields.Many2one('hr.employee', string='Checked By Name', help='For Approved by name')
    check_by_date = fields.Date(string='Checked Date', help='For Approved By Position',
                                default=fields.Date.context_today)

    verified_by_sign = fields.Binary(string='Deliver Sign', help='For Delivery By Sign')
    verified_by_name = fields.Many2one('hr.employee', string='Verified Name ', help='Deliver BY Name')
    verified_by_date = fields.Date(string='Verified Date', help='For Deliver By Position',
                                   default=fields.Date.context_today)

    approved_by_sign = fields.Binary(string='Approved Sign', help='for approved by sign')
    approved_by_name = fields.Many2one('hr.employee', string='Approved Name', help='For Approved by name')
    approved_by_date = fields.Date(string='Approved Date', help='For Approved By Position',
                                   default=fields.Date.context_today)

    # FOR GROUPBY (PRODUCT_ID AND BRAND_ID)
    product_id = fields.Many2one('product.product', related='purchase_requisition_line.product_id', string='Product')
    brand_id = fields.Many2one('product.brand', related='purchase_requisition_line.brand_id', string='Brand',
                               store=True)

    is_confirm = fields.Boolean(string='Confirmed', default=False, copy=False)
    is_verified = fields.Boolean(string='Verified', default=False, copy=False)
    is_checked = fields.Boolean(string='Checked', default=False, copy=False)
    is_approved = fields.Boolean(string='Approved', default=False, copy=False)

    is_access_confirm = fields.Boolean('Access Confirm', compute='_check_access')
    is_access_verified = fields.Boolean('Access Verified', compute='_check_access')
    is_access_checked = fields.Boolean('Access Checked', compute='_check_access')
    is_access_approve = fields.Boolean('Access Approved', compute='_check_access')
    is_access_cancel = fields.Boolean('Access Cancel', compute='_check_access')

    def _check_access(self):
        self.is_access_confirm = self.is_access_verified = self.is_access_checked= self.is_access_approve = self.is_access_cancel = False
        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])
            if employee_id:
                if employee_id.is_purchase_req_confirm:
                    self.is_access_confirm = True
                if employee_id.is_purchase_req_verified:
                    self.is_access_verified = True
                if employee_id.is_purchase_req_checked:
                    self.is_access_checked = True
                if employee_id.is_purchase_req_approved:
                    self.is_access_approve = True
                if employee_id.is_purchase_req_cancel:
                    self.is_access_cancel = True

    @api.onchange('login_employee_id')
    def onchange_login_employee_id(self):
        if self.login_employee_id:
            self._check_access()

    @api.onchange('request_date')
    def onchange_request_date(self):
        user_id = self.env.user
        self.department_id = user_id.employee_id.department_id.id

    def unlink(self):
        if not 'draft' in self.mapped('state'):
            raise UserError(_('You cannot delete Product Line which is Approved.'))
        return super(PurchaseStockRequisition, self).unlink()

    @api.model
    def create(self, vals):
        short_code = self.env['res.company'].browse(vals['company_id']).short_code
        if not short_code:
            raise ValidationError('Please Insert Company Short Code in Company Setting')
        else:
            vals['reference_code'] = str(short_code) + '/' + self.env['ir.sequence'].next_by_code(
                'purchase.stock.requisition') or _('New')
        res = super(PurchaseStockRequisition, self).create(vals)
        return res

    def action_confirm(self):
        if self.is_confirm:
            raise ValidationError(
                _("This Record is already ( %s) . Please Refresh Your Browser Thanks!!!!" % (self.state)))

        lines = self.purchase_requisition_line.filtered(lambda line: not line.display_type)
        if not lines:
            raise UserError('!!!Please add at least one product line!!!')
        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])
            self.req_by_sign = employee_id.user_signature
            self.req_by_name = employee_id.id
        else:
            self.req_by_sign = self.env.user.employee_id.user_signature
            self.req_by_name = self.env.user.employee_id.id
        self.write({'state': 'requested'})
        self.is_confirm = True

    def action_verified(self):
        if self.is_verified:
            raise ValidationError(
                _("This Record is already ( %s) . Please Refresh Your Browser Thanks!!!!" % (self.state)))

        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])
            self.verified_by_sign = employee_id.user_signature
            self.verified_by_name = employee_id.id
        else:
            self.verified_by_sign = self.env.user.employee_id.user_signature
            self.verified_by_name = self.env.user.employee_id.id
        self.write({'state': 'verified'})
        self.is_verified = True

    def action_checked(self):

        if self.is_checked:
            raise ValidationError(
                _("This Record is already ( %s) . Please Refresh Your Browser Thanks!!!!" % (self.state)))
        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])
            self.check_by_sign = employee_id.user_signature
            self.check_by_name = employee_id.id
        else:
            self.check_by_sign = self.env.user.employee_id.user_signature
            self.check_by_name = self.env.user.employee_id.id
        self.write({'state': 'checked'})
        self.is_checked = True

    def action_approved(self):
        if self.is_approved:
            raise ValidationError(
                _("This Record is already ( %s) . Please Refresh Your Browser Thanks!!!!" % (self.state)))
        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])
            self.approved_by_sign = employee_id.user_signature
            self.approved_by_name = employee_id.id
        else:
            self.approved_by_sign = self.env.user.employee_id.user_signature
            self.approved_by_name = self.env.user.employee_id.id
        self.write({'state': 'approved'})
        self.is_approved = True

    def action_cancel(self):
        self.is_confirm = False
        self.is_verified = False
        self.is_checked = False
        self.is_approved = False
        self.write({'state': 'cancel'})


class PurchaseRequisitionLine(models.Model):
    _name = 'purchase.requisitions.line'
    _description = 'Purchase Requisition Line'
    _order = "reference_code desc"

    created_date = fields.Datetime(string='Created Date', default=fields.Datetime.now)
    sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of sale quote lines.",
                              default=10)
    purchase_requisitions_id = fields.Many2one('purchase.stock.requisition', string='Purchase Requisition', copy=False)
    product_id = fields.Many2one('product.product', string='Product',
                                 domain="[('product_family_id','=',parent.product_family_id)]")
    brand_id = fields.Many2one('product.brand', related='product_id.brand_id', string='Brand', store=True)
    name = fields.Text('Description ', translate=True)
    product_uom = fields.Many2one('uom.uom', 'UOM', related='product_id.uom_id', required=False)
    reference_code = fields.Char(string='Reference', related='purchase_requisitions_id.reference_code', store=True)
    stock_balance_qty = fields.Float('Stock Balance', default=0.0, digits='Product Stock Balance')
    required_qty = fields.Float('Required Qty', default=0.0, digits='Product Required Qty')
    allowed_qty = fields.Float('Allowed Qty', default=0.0, digits='Product Allowed Qty')
    expected_date = fields.Date(string='Expected Date', default=fields.Date.context_today)
    remark = fields.Text(string='Remark')
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")

    state = fields.Selection(
        related='purchase_requisitions_id.state', string='Requestion Status', copy=False, store=True)

    product_warranty_period = fields.Integer(string='Life Cycle Period')
    product_period = fields.Selection([('1', 'Months'), ('12', 'Years')],
                                      string='Number of Months in a Print Period', default='12')

    is_created_aggrement = fields.Boolean(string='Is Created', default=False)

    @api.onchange('product_id')
    def onchange_product(self):
        for rec in self:
            if rec.product_id:
                main_warehouse_id = self.env['stock.warehouse'].search([('is_main_wh', '=', True)], limit=1)
                # mwh_onhand_qty = self.env['stock.quant'].search(
                #     [('location_id.location_id', '=', main_warehouse_id.code)]).quantity
                mwh_onhand_qty = sum(
                    self.env['stock.quant']._gather(rec.product_id, main_warehouse_id.lot_stock_id).mapped('quantity'))
                rec.stock_balance_qty = mwh_onhand_qty
                rec.name = rec.product_id.get_product_multiline_description_sale()

    def write(self, values):
        first_qty = self.multi_allowed_qty
        change_qty = values.get('multi_allowed_qty')
        first_req_qty = self.multi_required_qty
        change_req_qty = values.get('multi_required_qty')
        first_muom_id = self.multi_uom_line_id.id
        change_muom_id = values.get('multi_uom_line_id')
        res = super(PurchaseRequisitionLine, self).write(values)
        if change_qty:
            if change_qty > 0 and first_qty != change_qty:

                message = (f"ALLOWED QTY: {first_qty} ==> {change_qty}.0")
                self.purchase_requisitions_id.message_post(body=message)
        if change_muom_id:
            if change_muom_id and change_muom_id != first_muom_id:
                first_uom = self.env['multi.uom.line'].browse(first_muom_id).uom_id.name
                change_uom = self.env['multi.uom.line'].browse(change_muom_id).uom_id.name
                message = (f"MUOM: {first_uom} ==> {change_uom}.")
                self.purchase_requisitions_id.message_post(body=message)

        if change_req_qty and not change_muom_id:
            if change_req_qty > 0 and first_req_qty != change_req_qty:
                message = (f"REQUIRED QTY: {first_req_qty} ==> {change_req_qty}.0")
                self.purchase_requisitions_id.message_post(body=message)

        if 'display_type' in values and self.filtered(lambda line: line.display_type != values.get('display_type')):
            raise UserError(
                _("You cannot change the type of a sale quote line. Instead you should delete the current line and create a new line of the proper type."))
        return res

    def unlink(self):
        if not 'draft' in self.mapped('state'):
            raise UserError(_('You cannot delete Product Line which is Approved.'))
        return super(PurchaseRequisitionLine, self).unlink()

    # overwrite in multi_uom
    def action_purchase_agreement(self):
        agreement_lines = []
        active_ids = self.env.context.get('active_ids', [])
        lines = self.env['purchase.requisitions.line'].browse(active_ids)
        lines = lines.sorted(key=lambda l: (l.product_id.id, l.product_uom.id))
        purchase_agreement = self.env['purchase.requisition'].create({
            'ordering_date': Date.today(),

        })
        for key, grouped_lines in groupby(lines, lambda l: (l.product_id.id, l.product_uom.id)):
            allowed_qty = 0
            req_qty = 0
            first_line = False
            for line in grouped_lines:
                allowed_qty += line.allowed_qty
                req_qty += line.required_qty
                first_line = line
            agreement_lines.append({
                'product_id': first_line.product_id.id,
                'product_description_variants': first_line.name,
                'required_qty': req_qty,
                'product_qty': allowed_qty,
                'product_uom_id': first_line.product_uom.id,
                'multi_uom_line_id':first_line.multi_uom_line_id.id,
                'schedule_date': first_line.expected_date,
                'requisition_id': purchase_agreement.id,
                'product_warranty_period': first_line.product_warranty_period,
                'product_period': first_line.product_period,
                'remark': first_line.remark
            })

        self.env['purchase.requisition.line'].create(agreement_lines)
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Converted To Purchase Agreement',
                'type': 'rainbow_man',
            }
        }
