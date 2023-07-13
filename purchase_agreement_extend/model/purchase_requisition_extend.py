from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PurchaseRequisition(models.Model):
    _inherit = "purchase.requisition"

    requisition_id = fields.Many2one('purchase.stock.requisition', string='REQ')
    active_currency = fields.Boolean('Apply Currency', default=False)
    manual_base_rate = fields.Float(digits=0, default=1.0, string='Exchange Rate')

    def action_in_progress(self):
        self.ensure_one()
        if not self.vendor_id:
            raise UserError(
                _("Please Select a Vendor!!"))

        if not self.line_ids:
            raise UserError(_("You cannot confirm agreement '%s' because there is no product line.", self.name))

        if self.type_id.quantity_copy == 'none' and self.vendor_id:
            for requisition_line in self.line_ids:
                if requisition_line.price_unit <= 0.0:
                    raise UserError(_('You cannot confirm the blanket order without price.'))
                if requisition_line.product_qty <= 0.0:
                    raise UserError(_('You cannot confirm the blanket order without quantity.'))
                requisition_line.create_supplier_info()
            self.write({'state': 'ongoing'})
        else:
            self.write({'state': 'in_progress'})
        # Set the sequence number regarding the requisition type
        if self.name == 'New':
            short_code = self.company_id.short_code
            if not short_code:
                raise ValidationError('Please Insert Company Short Code in Company Setting')
            else:
                self.name = str(short_code) + '/' + self.env['ir.sequence'].next_by_code('purchase.requisition')

    @api.onchange('vendor_id')
    def onchange_supplier(self):
        for rec in self:
            rec.line_ids.property_supplier_payment_term_id = rec.vendor_id.property_supplier_payment_term_id.id

    @api.onchange('manual_base_rate')
    def onchange_base_rate(self):
        return self.line_ids.onchange_discount()

    def write(self, values):
        res = super(PurchaseRequisition, self).write(values)
        if not self.vendor_id:
            raise UserError(
                _("Please Select a Vendor!!"))
        return res


class PurchaseRequisitionLine(models.Model):
    _inherit = "purchase.requisition.line"

    requisition_id = fields.Many2one('purchase.requisition', string='Purchase Requisition')

    discount_type = fields.Selection(selection=[('percentage', 'Percentage'), ('fixed', 'Fixed')], string='Disc Type',
                                     default="fixed")
    discount = fields.Float(string="Dis/Refund")
    discount_amount = fields.Float(string="Dis Amt", compute='_get_discount_amount', store=True)
    amount_mmk = fields.Float(string='Amount MMK')
    product_warranty_period = fields.Integer(string='Life Cycle Period')
    product_period = fields.Selection([('1', 'Months'), ('12', 'Years')],
                                      string='Number of Months in a Print Period', default='12')

    taxes_id = fields.Many2many('account.tax', string='Taxes',
                                domain=['|', ('active', '=', False), ('active', '=', True)])
    remark = fields.Text(string='Remark')
    brand_id = fields.Many2one('product.brand', related='product_id.brand_id', string='Brand')
    unit_price_mmk = fields.Float(string='Unit Price MMK', compute='_get_unit_price_mmk')
    other_charges = fields.Float(string='Other Charges')
    property_supplier_payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms')
    required_qty = fields.Float('Required Qty', default=0.0, digits='Product Required Qty')
    base_rate_data = fields.Float(related='requisition_id.manual_base_rate', string='Rate', store=True)

    state = fields.Selection(
        related='requisition_id.state', string='Purchase Requisition Status', copy=False, store=True)

    @api.onchange('discount_amount', 'discount', 'discount_type', 'price_unit', 'product_qty', )
    def onchange_discount(self):
        for rec in self:
            if rec.requisition_id.currency_id.name != 'MMK':
                total_amount_mmk = (rec.product_qty * rec.price_unit) - rec.discount_amount
                if rec.requisition_id.active_currency:
                    rec.amount_mmk = rec.requisition_id.manual_base_rate * total_amount_mmk
                else:
                    price_unit = 1
                    price_unit = rec.requisition_id.currency_id._convert(
                        price_unit, rec.requisition_id.company_id.currency_id, rec.requisition_id.company_id,
                        fields.Date.context_today(self),
                        round=False)
                    rec.amount_mmk = total_amount_mmk * price_unit
            else:
                rec.amount_mmk = (rec.product_qty * rec.price_unit) - rec.discount_amount

    @api.depends('price_unit')
    def _get_unit_price_mmk(self):
        for rec in self:
            rec.unit_price_mmk = 0.00

            if rec.requisition_id.currency_id.name != 'MMK':
                if rec.requisition_id.active_currency:
                    rec.unit_price_mmk = rec.requisition_id.manual_base_rate * rec.price_unit
                else:
                    price_unit = 1
                    price_unit = rec.requisition_id.currency_id._convert(
                        price_unit, rec.requisition_id.company_id.currency_id, rec.requisition_id.company_id,
                        fields.Date.context_today(self),
                        round=False)
                    rec.unit_price_mmk = rec.price_unit * price_unit
            else:
                rec.unit_price_mmk = rec.price_unit

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

    def unlink(self):
        if not 'draft' in self.mapped('state'):
            raise UserError(_('You cannot delete Product Line which is Approved.'))
        return super(PurchaseRequisitionLine, self).unlink()
