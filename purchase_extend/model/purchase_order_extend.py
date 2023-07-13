from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Date
from odoo.http import request
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    submission_id = fields.Many2one('submission.quotation', string='Submission', copy=False)

    submission_no = fields.Char(string='Submission No')

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
    state = fields.Selection(selection_add=[('to approve', 'To Approve'),
                                            ('confirm', 'Confirm'),
                                            ('verified', 'Verified'),
                                            ('purchase', 'Purchased')])
    to_approve_id = fields.Many2one('hr.employee', string='To Approve')
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True, states=READONLY_STATES,
                                 change_default=True, tracking=True,
                                 domain="[('supplier','=', True)]",
                                 help="You can find a vendor by its Name, TIN, Email or Internal Reference.")

    user_id = fields.Many2one('res.users', string='To Approve', tracking=True, default=False)

    is_access_confirm = fields.Boolean('Access Confirm', compute='_check_access')
    is_access_verified = fields.Boolean('Access Verified', compute='_check_access')
    is_access_approve = fields.Boolean('Access Approved', compute='_check_access')
    is_access_cancel = fields.Boolean('Access Cancel', compute='_check_access')

    def _check_access(self):
        self.is_access_confirm = self.is_access_verified = self.is_access_approve = self.is_access_cancel = False
        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])
            if employee_id:
                if employee_id.is_po_confirm:
                    self.is_access_confirm = True
                if employee_id.is_po_verified:
                    self.is_access_verified = True
                if employee_id.is_po_approved:
                    self.is_access_approve = True
                if employee_id.is_po_cancel:
                    self.is_access_cancel = True

    @api.model
    def default_get(self, fields_list):
        vals = super(PurchaseOrder, self).default_get(fields_list)
        default_analytic_account_id = False
        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])
            if employee_id:
                analytic_id = employee_id.def_analytic_account_id.id
                if analytic_id:
                    default_analytic_account_id = analytic_id
        if default_analytic_account_id:
            vals.update({'analytic_account_id': default_analytic_account_id})
        return vals

    @api.onchange('login_employee_id', 'analytic_account_id')
    def onchange_login_employee(self):
        self._check_access()
        for rec in self:
            if request.session.emp_id:
                data = int(request.session.emp_id)
                employee_id = self.env['hr.employee'].search([('id', '=', data)])

                if employee_id:
                    analytic_ids = employee_id.allow_analytic_account_id.ids
                    return {'domain': {'analytic_account_id': [('id', 'in', analytic_ids)]}}
            else:
                return {'domain': {'analytic_account_id': []}}

    def unlink(self):
        if not 'draft' in self.mapped('state'):
            raise UserError(_('You cannot delete Product Line which is Approved.'))
        return super(PurchaseOrder, self).unlink()

    def action_confirm(self):
        lines = self.order_line.filtered(lambda line: not line.display_type)
        if not lines:
            raise UserError('!!!Please add at least one product line!!!')
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

    def action_verified(self):
        if not self.user_id:
            raise UserError(_('Approval Person is missing .Please Choose an Approval Person Thanks!!'))
        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])
            self.verified_by_sign = employee_id.user_signature
            self.verified_by_name = employee_id.id
        else:
            self.verified_by_sign = self.env.user.employee_id.user_signature
            self.verified_by_name = self.env.user.employee_id.id

        self.verified_by_date = Date.today()
        self.write({'state': 'verified'})

    def button_confirm(self):
        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])
            self.approved_by_sign = employee_id.user_signature
            self.approved_by_name = employee_id.id
        else:
            self.approved_by_sign = self.env.user.employee_id.user_signature
            self.approved_by_name = self.env.user.employee_id.id

        self.approved_by_date = Date.today()
        for order in self:
            order._add_supplier_to_product()
            # Deal with double validation process
            if order.company_id.po_double_validation == 'one_step' \
                    or (order.company_id.po_double_validation == 'two_step' \
                        and order.amount_total < self.env.user.company_id.currency_id.compute(
                        order.company_id.po_double_validation_amount, order.currency_id)) \
                    or order.user_has_groups('purchase.group_purchase_manager'):
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
            order.picking_ids.write({'analytic_account_id': order.analytic_account_id.id})
        return True

    @api.model
    def create(self, vals):
        short_code = self.env['res.company'].browse(vals['company_id']).short_code
        if not short_code:
            raise ValidationError('Please Insert Company Short Code')
        else:
            vals['name'] = str(short_code) + '/' + self.env['ir.sequence'].next_by_code('purchase.order.seq') or _(
                'New')

        res = super(PurchaseOrder, self).create(vals)
        return res


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    discount_type = fields.Selection(selection=[('percentage', 'Percentage'), ('fixed', 'Fixed')], string='Disc Type',
                                     default="fixed")
    discount = fields.Float(string="Dis/Refund")
    discount_amount = fields.Float(string="Dis Amt", compute='_get_discount_amount', store=True)
    country_origin = fields.Char(string='Country Of Origin')

    @api.depends('price_unit', 'product_qty', 'discount_type', 'discount')
    def _get_discount_amount(self):
        for record in self:
            if record.discount_type == 'percentage':
                discount_amt = record.price_unit * ((record.discount or 0.0) / 100.0) * record.product_qty

            else:
                discount_amt = record.product_qty * record.discount
            record.update({
                'discount_amount': discount_amt
            })

    @api.depends('product_qty', 'price_unit', 'taxes_id', 'discount_type', 'discount', 'discount_amount')
    def _compute_amount(self):
        return super(PurchaseOrderLine, self)._compute_amount()

    def _prepare_compute_all_values(self):
        res = super(PurchaseOrderLine, self)._prepare_compute_all_values()
        price_unit = res['price_unit']
        product_qty = res['quantity']

        if self.discount_type == 'percentage':
            price_unit = price_unit * (1 - (self.discount or 0.0) / 100.0)
        else:
            price_unit = (price_unit * product_qty) - (self.discount * product_qty)
            product_qty = 1.0

        res['price_unit'] = price_unit
        res['quantity'] = product_qty
        return res

    def _prepare_account_move_line(self, move=False):
        res = super(PurchaseOrderLine, self)._prepare_account_move_line(move=move)
        res.update({
            'discount_type': self.discount_type,
            'discount': self.discount,
            'discount_amount': self.discount_amount,
        })
        return res

    def unlink(self):
        if not 'draft' in self.mapped('state'):
            raise UserError(_('You cannot delete Product Line which is Approved.'))
        return super(PurchaseOrderLine, self).unlink()

    def write(self, values):
        old_uom = self.multi_uom_line_id.uom_id.name
        old_purchase_uom_qty =self.purchase_uom_qty
        result = super(PurchaseOrderLine, self).write(values)
        if 'product_qty' in values or 'purchase_uom_id' in values:
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            for line in self:
                if (line.order_id.state == "purchase" and float_compare(line.product_qty, values["product_qty"], precision_digits=precision) != 0):

                    line.order_id.message_post_with_view('purchase.track_po_line_template',
                                                         values={'line': line, 'product_qty': values['product_qty']},
                                                         subtype_id=self.env.ref('mail.mt_note').id)
                if line.order_id.state == "purchase" and "multi_uom_line_id" in values:

                    new_uom = self.env['multi.uom.line'].browse(values['multi_uom_line_id']).uom_id.name
                    line.order_id.message_post_with_view('purchase.track_po_line_template',
                                                         values={'line': line, 'new_uom':old_uom },
                                                         subtype_id=self.env.ref('mail.mt_note').id)
                if line.order_id.state == "purchase" and "purchase_uom_qty" in values:
                    line.order_id.message_post_with_view('purchase.track_po_line_template',
                                                         values={'line': line, 'old_purchase_uom_qty': old_purchase_uom_qty},
                                                         subtype_id=self.env.ref('mail.mt_note').id)



        return result


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    discount_type = fields.Selection(selection=[('percentage', 'Percentage'), ('fixed', 'Fixed')],
                                     string='Disc Type', default="fixed")
    discount = fields.Float(string="Dis/Refund")
    discount_amount = fields.Float(string="Dis Amt", compute='_get_discount_amount', store=True)

    @api.depends('price_unit', 'quantity', 'discount_type', 'discount')
    def _get_discount_amount(self):
        for record in self:
            if record.discount_type == 'percentage':
                discount_amt = record.price_unit * ((record.discount or 0.0) / 100.0) * record.quantity
            else:
                discount_amt = record.quantity * record.discount

            record.update({
                'discount_amount': discount_amt
            })

    @api.model
    def _get_price_total_and_subtotal_model(self, price_unit, quantity, discount, currency, product, partner, taxes,
                                            move_type):
        ''' This method is used to compute 'price_total' & 'price_subtotal'.

        :param price_unit:  The current price unit.
        :param quantity:    The current quantity.
        :param discount:    The current discount.
        :param currency:    The line's currency.
        :param product:     The line's product.
        :param partner:     The line's partner.
        :param taxes:       The applied taxes.
        :param move_type:   The type of the move.
        :return:            A dictionary containing 'price_subtotal' & 'price_total'.
        '''
        res = {}

        # Compute 'price_subtotal'.
        discount_type = ''

        if self._context and self._context.get('wk_vals_list', []):
            for vals in self._context.get('wk_vals_list', []):
                if price_unit == vals.get('price_unit', 0.0) and quantity == vals.get('quantity',
                                                                                      0.0) and discount == vals.get(
                    'discount', 0.0) and product.id == vals.get('product_id', False) and partner.id == vals.get(
                    'partner_id', False):
                    discount_type = vals.get('discount_type', '')
        discount_type = self.discount_type or discount_type or ''

        if discount_type == 'fixed':
            line_discount_price_unit = price_unit * quantity - (discount * quantity)
            quantity = 1.0
        else:
            line_discount_price_unit = price_unit * (1 - (discount / 100.0))
        subtotal = quantity * line_discount_price_unit

        # Compute 'price_total'.
        if taxes:
            force_sign = -1 if move_type in ('out_invoice', 'in_refund', 'out_receipt') else 1
            taxes_res = taxes._origin.with_context(force_sign=force_sign).compute_all(line_discount_price_unit,
                                                                                      quantity=quantity,
                                                                                      currency=currency,
                                                                                      product=product, partner=partner,
                                                                                      is_refund=move_type in (
                                                                                          'out_refund', 'in_refund'))
            res['price_subtotal'] = taxes_res['total_excluded']
            res['price_total'] = taxes_res['total_included']
        else:
            res['price_total'] = res['price_subtotal'] = subtotal

        # In case of multi currency, round before it's use for computing debit credit
        if currency:
            res = {k: currency.round(v) for k, v in res.items()}
        return res

    @api.model
    def _get_fields_onchange_balance_model(self, quantity, discount, amount_currency, move_type, currency, taxes,
                                           price_subtotal, force_computation=False):
        ''' This method is used to recompute the values of 'quantity', 'discount', 'price_unit' due to a change made
        in some accounting fields such as 'balance'.

        This method is a bit complex as we need to handle some special cases.
        For example, setting a positive balance with a 100% discount.

        :param quantity:        The current quantity.
        :param discount:        The current discount.
        :param balance:         The new balance.
        :param move_type:       The type of the move.
        :param currency:        The currency.
        :param taxes:           The applied taxes.
        :param price_subtotal:  The price_subtotal.
        :return:                A dictionary containing 'quantity', 'discount', 'price_unit'.
        '''
        balance_form = 'credit' if amount_currency > 0 else 'debit'
        if move_type in self.move_id.get_outbound_types():
            sign = 1
        elif move_type in self.move_id.get_inbound_types():
            sign = -1
        else:
            sign = 1
        amount_currency *= sign

        # Avoid rounding issue when dealing with price included taxes. For example, when the price_unit is 2300.0 and
        # a 5.5% price included tax is applied on it, a balance of 2300.0 / 1.055 = 2180.094 ~ 2180.09 is computed.
        # However, when triggering the inverse, 2180.09 + (2180.09 * 0.055) = 2180.09 + 119.90 = 2299.99 is computed.
        # To avoid that, set the price_subtotal at the balance if the difference between them looks like a rounding
        # issue.
        if not force_computation and currency.is_zero(amount_currency - price_subtotal):
            return {}

        taxes = taxes.flatten_taxes_hierarchy()
        if taxes and any(tax.price_include for tax in taxes):

            # Inverse taxes. E.g:
            #
            # Price Unit    | Taxes         | Originator Tax    |Price Subtotal     | Price Total
            # -----------------------------------------------------------------------------------
            # 110           | 10% incl, 5%  |                   | 100               | 115
            # 10            |               | 10% incl          | 10                | 10
            # 5             |               | 5%                | 5                 | 5
            #
            # When setting the balance to -200, the expected result is:
            #
            # Price Unit    | Taxes         | Originator Tax    |Price Subtotal     | Price Total
            # -----------------------------------------------------------------------------------
            # 220           | 10% incl, 5%  |                   | 200               | 230
            # 20            |               | 10% incl          | 20                | 20
            # 10            |               | 5%                | 10                | 10

            force_sign = -1 if move_type in ('out_invoice', 'in_refund', 'out_receipt') else 1
            taxes_res = taxes._origin.with_context(force_sign=force_sign).compute_all(amount_currency,
                                                                                      currency=currency,
                                                                                      handle_price_include=False)
            for tax_res in taxes_res['taxes']:
                tax = self.env['account.tax'].browse(tax_res['id'])
                if tax.price_include:
                    amount_currency += tax_res['amount']

        discount_type = ''
        if self._context and self._context.get('wk_vals_list', []):
            for vals in self._context.get('wk_vals_list', []):
                if quantity == vals.get('quantity', 0.0) and discount == vals.get('discount',
                                                                                  0.0) and amount_currency == vals.get(
                    balance_form, 0.0):
                    discount_type = vals.get('discount_type', '')
        discount_type = self.discount_type or discount_type or ''
        if discount_type == 'fixed':
            if amount_currency:
                vals = {
                    'quantity': quantity or 1.0,
                    'price_unit': (amount_currency + discount) / (quantity or 1.0),
                }
            else:
                vals = {'price_unit': 0.0}
        else:
            discount_factor = 1 - (discount / 100.0)
            if amount_currency and discount_factor:
                # discount != 100%
                vals = {
                    'quantity': quantity or 1.0,
                    'price_unit': amount_currency / discount_factor / (quantity or 1.0),
                }
            elif amount_currency and not discount_factor:
                # discount == 100%
                vals = {
                    'quantity': quantity or 1.0,
                    'discount': 0.0,
                    'price_unit': amount_currency / (quantity or 1.0),
                }
            elif not discount_factor:
                # balance of line is 0, but discount  == 100% so we display the normal unit_price
                vals = {}
            else:
                # balance is 0, so unit price is 0 as well
                vals = {'price_unit': 0.0}
        return vals

    @api.onchange('quantity', 'discount', 'discount_type', 'price_unit', 'tax_ids')
    def _onchange_price_subtotal(self):
        return super(AccountMoveLine, self)._onchange_price_subtotal()

    @api.model_create_multi
    def create(self, vals_list):
        context = self._context.copy()
        context.update({'wk_vals_list': vals_list})
        res = super(AccountMoveLine, self.with_context(context)).create(vals_list)
        return res
