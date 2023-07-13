from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Date
from odoo.http import request
from itertools import groupby


class SubmissionQuotation(models.Model):
    _name = 'submission.quotation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'For Purchase Order Submission of Quotation'
    _rec_name = 'reference_code'
    _order = 'id desc'

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company,
                                 required=True, )
    reference_code = fields.Char(string='Reference Code')

    submission_line_ids = fields.One2many('submission.quotation.line', 'submission_id', string='Submission Lines')
    state = fields.Selection(
        [('draft', 'Draft'),
         ('submit', 'Submit'),
         ('confirm', 'Confirm'),
         ('checked', 'Checked'),
         ('approved', 'Approved'),
         ('cancel', 'Canceled')], string='State', default='draft', tracking=True)
    partner_id = fields.Many2one('res.partner', related='submission_line_ids.supplier_id', store=True)
    prepare_by_sign = fields.Binary(string='Prepare Sign', help='For Req By Sign')
    prepare_by_name = fields.Many2one('hr.employee', string='prepare Name', help='For Req By Name')
    prepare_by_date = fields.Date(string='Prepare By Date', help='For Req By Position',
                                  default=fields.Date.context_today)

    confirm_by_sign = fields.Binary(string='Confirm By Sign', help='for approved by sign')
    confirm_by_name = fields.Many2one('hr.employee', string='Confirm By Name', help='For Approved by name')
    confirm_by_date = fields.Date(string='Confirm Date', help='For Approved By Position',
                                  default=fields.Date.context_today)

    verified_by_sign = fields.Binary(string='Deliver Sign', help='For Delivery By Sign')
    verified_by_name = fields.Many2one('hr.employee', string='Verified Name ', help='Deliver BY Name')
    verified_by_date = fields.Date(string='Verified Date', help='For Deliver By Position',
                                   default=fields.Date.context_today)

    approved_by_sign = fields.Binary(string='Approved Sign', help='for approved by sign')
    approved_by_name = fields.Many2one('hr.employee', string='Approved Name', help='For Approved by name')
    approved_by_date = fields.Date(string='Approved Date', help='For Approved By Position',
                                   default=fields.Date.context_today)

    order_count = fields.Integer(compute='_compute_orders_number', string='Number of Orders')
    user_id = fields.Many2one('res.users', string='To Approve')

    is_submit = fields.Boolean(string='Submitted', default=False, copy=False)
    is_confirm = fields.Boolean(string='Confirmed', default=False, copy=False)
    is_checked = fields.Boolean(string='Checked', default=False, copy=False)

    is_access_submit = fields.Boolean('Access Submit', compute='_check_access')
    is_access_confirm = fields.Boolean('Access Confirm', compute='_check_access')
    is_access_check = fields.Boolean('Access Check', compute='_check_access')
    is_access_approve = fields.Boolean('Access Approved', compute='_check_access')
    is_access_cancel = fields.Boolean('Access Cancel', compute='_check_access')

    def _check_access(self):
        self.is_access_submit = self.is_access_confirm = self.is_access_check = self.is_access_approve = self.is_access_cancel = False
        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])
            if employee_id:
                if employee_id.is_submit_access:
                    self.is_access_submit = True
                if employee_id.is_confirm_access:
                    self.is_access_confirm = True
                if employee_id.is_check_access:
                    self.is_access_check = True
                if employee_id.is_approve_access:
                    self.is_access_approve = True
                if employee_id.is_cancel_access:
                    self.is_access_cancel = True

    @api.onchange('login_employee_id')
    def onchange_login_employee_id(self):
        if self.login_employee_id:
            self._check_access()

    @api.depends('submission_line_ids')
    def _compute_orders_number(self):
        for requisition in self:
            purchase_order_line = self.env['purchase.order'].search([('submission_id', '=', self.id)])
            requisition.order_count = len(purchase_order_line)

    @api.model
    def create(self, vals):
        short_code = self.env['res.company'].browse(vals['company_id']).short_code
        if not short_code:
            raise ValidationError('Please Insert Company Short Code')
        else:
            vals['reference_code'] = str(short_code) + '/' + self.env['ir.sequence'].next_by_code(
                'submission.quotation') or _(
                'New')
        res = super(SubmissionQuotation, self).create(vals)
        return res

    def unlink(self):
        if not 'draft' in self.mapped('state'):
            raise UserError(_('You cannot delete Product Line which is Approved.'))
        return super(SubmissionQuotation, self).unlink()

    def action_submit(self):
        if self.is_submit:
            raise ValidationError(
                _("This Record is already ( %s) . Please Refresh Your Browser Thanks!!!!" % (self.state)))
        lines = self.submission_line_ids.filtered(lambda line: not line.display_type)
        if not lines:
            raise UserError('!!!Please add at least one product line!!!')
        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])
            self.prepare_by_sign = employee_id.user_signature
            self.prepare_by_name = employee_id.id
        else:
            self.prepare_by_sign = self.env.user.employee_id.user_signature
            self.prepare_by_name = self.env.user.employee_id.id
        self.prepare_by_date = Date.today()
        self.write({'state': 'submit'})
        self.is_submit = True

    def action_confirm(self):
        if self.is_confirm:
            raise ValidationError(
                _("This Record is already ( %s) . Please Refresh Your Browser Thanks!!!!" % (self.state)))
        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])
            self.confirm_by_sign = employee_id.user_signature
            self.confirm_by_name = employee_id.id
        else:
            self.confirm_by_sign = self.env.user.employee_id.user_signature
            self.confirm_by_name = self.env.user.employee_id.id
        self.confirm_by_date = Date.today()
        self.write({'state': 'confirm'})
        self.is_confirm = True

    def action_checked(self):
        if self.is_checked:
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
        self.verified_by_date = Date.today()
        self.write({'state': 'checked'})
        self.is_checked = True

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_open_purchase_order(self):

        return {
            'type': 'ir.actions.act_window',
            'name': ('Purchase Order'),
            'res_model': 'purchase.order',
            'view_mode': 'tree,form,kanban,pivot,graph',
            'domain': [('submission_id', '=', self.id)],
            'context': {}
        }

    def _prepare_picking_values(self):
        self.ensure_one()
        lines = self.submission_line_ids.filtered(
            lambda line: line.confirm_to_purchase == 'yes')
        return {
            'submission_no': self.reference_code,
            'submission_id': self.id,
            'partner_id': lines.supplier_id.id
        }

    @api.constrains('submission_line_ids.confirm_to_purchase')
    def check_confirm_purchase(self):
        for rec in self.submission_line_ids:
            if rec.confirm_to_purchase == False:
                raise UserError(_("Can't Approved, Please Set value 'Yes' or 'No' in Confirm To Purchase"))

    def action_approved(self):
        self.check_confirm_purchase()
        lines = self.submission_line_ids.filtered(
            lambda line: not line.display_type and line.confirm_to_purchase == 'yes')
        if not lines:
            raise UserError(
                "Can't Approved, The value of Confirm To Purchase must have at least one 'Yes' in Product Lines!")
        check_already_approved = self.env['purchase.order'].search([('submission_id', '=', self.id)])
        if not check_already_approved:
            data = {}

            for line in lines:
                key = f'{line.supplier_id.id}-{line.currency_id.id}'
                prev_records = data.get(key, [])
                prev_records.append(line)
                data[key] = prev_records

            for key, records in data.items():
                po_lines = []
                first_line = records[0]
                for rec in records:
                    po_lines.append((0, 0, {
                        'product_id': rec.product_id.id,
                        'name': rec.name,
                        'product_qty': rec.allowed_qty * rec.multi_uom_line_id.ratio,
                        'purchase_uom_qty': rec.allowed_qty,
                        'multi_uom_line_id': rec.multi_uom_line_id.id,
                        'multi_price_unit': rec.price_unit,
                        'taxes_id': rec.taxes_id.ids,
                        'date_planned': Date.today(),
                        'price_subtotal': rec.amount_mmk,
                        'discount_type': rec.discount_type,
                        'discount': rec.discount,
                        'discount_amount': rec.discount_amount,
                    }))
                self.env['purchase.order'].create({
                    'submission_no': self.reference_code,
                    'partner_id': first_line.supplier_id.id,
                    'company_id': self.env.company.id,
                    # 'manual_base_rate': first_line.purchase_agreement_id.manual_base_rate,
                    'submission_id': self.id,
                    'currency_id': first_line.currency_id.id,
                    'order_line': po_lines,
                    'login_employee_id': first_line.purchase_agreement_id.login_employee_id.id,
                    'prepare_by_sign': self.prepare_by_sign,
                    'prepare_by_name': self.prepare_by_name.id,
                    'prepare_by_date': self.prepare_by_date,

                })

            if request.session.emp_id:
                employee_id = self.env['hr.employee'].browse(int(request.session.emp_id))
            else:
                employee_id = self.env.user.employee_id
            self.approved_by_sign = employee_id.user_signature
            self.approved_by_name = employee_id.id
            self.approved_by_date = Date.today()
            self.write({'state': 'approved'})


class SubmissionQuotationLine(models.Model):
    _name = 'submission.quotation.line'
    _description = "Submission Quotation Line"

    submission_id = fields.Many2one('submission.quotation', string='Submission')
    sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of sale quote lines.",
                              default=10)
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    product_id = fields.Many2one('product.product', string='Product')
    purchase_agreement_id = fields.Many2one('purchase.requisition', string='Purchase Agreement No')
    brand_id = fields.Many2one('product.brand', string='Brand')
    supplier_id = fields.Many2one('res.partner', string='Supplier')
    name = fields.Text('Description ', translate=True)
    product_uom = fields.Many2one('uom.uom', 'UOM', related='product_id.uom_id', required=False, store=True)
    required_qty = fields.Float('Required Qty', default=0.0, digits='Product Required Qty')
    allowed_qty = fields.Float('Allowed Qty', default=0.0, digits='Product Allowed Qty')
    currency_id = fields.Many2one('res.currency', string='Currency')
    price_unit = fields.Float(string='Unit Price', digits='Product Price')
    discount_type = fields.Selection(selection=[('percentage', 'Percentage'), ('fixed', 'Fixed')], string='Disc Type',
                                     default="fixed")
    discount = fields.Float(string="Dis/Refund")
    discount_amount = fields.Float(string="Dis Amt", compute='_get_discount_amount', store=True)
    amount_mmk = fields.Float(string='Amount MMK')
    taxes_id = fields.Many2many('account.tax', string='Taxes',
                                domain=['|', ('active', '=', False), ('active', '=', True)])
    unit_price_mmk = fields.Float(string='Unit Price MMK')
    other_charges = fields.Float(string='Other Charges')
    product_warranty_period = fields.Integer(string='Life Cycle Period')
    product_period = fields.Selection([('1', 'Months'), ('12', 'Years')],
                                      string='Number of Months in a Print Period', default='12')
    remark = fields.Text(string='Remark')
    confirm_to_purchase = fields.Selection(
        [('yes', 'Yes'),
         ('no', 'No')], string='Confirm To Purchase')
    property_supplier_payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms')
    vendor_id = fields.Many2one('res.partner', related='purchase_agreement_id.vendor_id')

    state = fields.Selection(
        related='submission_id.state', string='Submission Status', copy=False, store=True)

    def write(self, values):
        first_qty = self.allowed_qty
        change_qty = values.get('allowed_qty')
        first_req_qty = self.required_qty
        change_req_qty = values.get('required_qty')
        res = super(SubmissionQuotationLine, self).write(values)
        if change_qty:
            if change_qty > 0 and first_qty != change_qty:
                message = (f"ALLOWED QTY: {first_qty} ==> {change_qty}.0")
                self.submission_id.message_post(body=message)
        if change_req_qty:
            if change_req_qty > 0 and first_req_qty != change_req_qty:
                message = (f"REQUIRED QTY: {first_req_qty} ==> {change_req_qty}.0")
                self.submission_id.message_post(body=message)

        if 'display_type' in values and self.filtered(lambda line: line.display_type != values.get('display_type')):
            raise UserError(
                _("You cannot change the type of a SQ line. Instead you should delete the current line and create a new line of the proper type."))
        return res

    def unlink(self):
        if not 'draft' in self.mapped('state'):
            raise UserError(_('You cannot delete Product Line which is Approved.'))
        return super(SubmissionQuotationLine, self).unlink()

    @api.depends('price_unit', 'allowed_qty', 'discount_type', 'discount')
    def _get_discount_amount(self):
        for record in self:
            if record.discount_type == 'percentage':
                discount_amt = record.price_unit * ((record.discount or 0.0) / 100.0) * record.allowed_qty

            else:
                discount_amt = record.allowed_qty * record.discount
            record.update({
                'discount_amount': discount_amt
            })

    @api.onchange('purchase_agreement_id')
    def onchange_agreement(self):
        product_list = self.purchase_agreement_id.line_ids.product_id.ids
        self.supplier_id = self.purchase_agreement_id.vendor_id.id
        return {'domain': {'product_id': [('id', '=', product_list)]}}

    @api.onchange('product_id')
    def onchange_product(self):
        for record in self:

            line = record.purchase_agreement_id.line_ids.filtered(lambda l: l.product_id.id == record.product_id.id)

            for rec in line:
                record.brand_id = rec.brand_id.id
                record.name = rec.product_description_variants
                record.product_uom = rec.product_uom_id.id
                record.multi_uom_line_id = rec.multi_uom_line_id.id
                record.allowed_qty = rec.product_qty
                record.required_qty = rec.qty_ordered
                record.currency_id = record.purchase_agreement_id.currency_id.id
                record.price_unit = rec.price_unit
                record.unit_price_mmk = rec.unit_price_mmk
                record.discount_type = rec.discount_type
                record.discount = rec.discount
                record.discount_amount = rec.discount_amount
                record.taxes_id = rec.taxes_id.ids
                record.amount_mmk = rec.amount_mmk
                record.other_charges = rec.other_charges
                record.property_supplier_payment_term_id = rec.property_supplier_payment_term_id.id
                record.product_warranty_period = rec.product_warranty_period
                record.product_period = rec.product_period
                record.remark = rec.remark
                record.required_qty = rec.required_qty
