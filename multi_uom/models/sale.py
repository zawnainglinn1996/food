from odoo import api, models, fields, _
from odoo.tools import is_html_empty
from datetime import timedelta

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_uom_qty = fields.Float(compute='compute_product_uom_qty',
                                   inverse='set_multi_uom_qty',
                                   store=True,
                                   readonly=False)
    qty_delivered_manual = fields.Float(compute='compute_manual_delivered_qty',
                                        inverse='set_multi_qty_delivered_manual',
                                        store=True)
    multi_uom_line_id = fields.Many2one('multi.uom.line', 'UoM')
    uom_ratio_remark = fields.Char(string='Ratio Remark', related='multi_uom_line_id.remark')
    multi_uom_qty = fields.Float('UOM Qty',
                                 digits='Product Unit of Measure',
                                 default=1.0)
    multi_qty_delivered = fields.Float('DeliveredQuantity',
                                       copy=False,
                                       compute='_compute_multi_qty_delivered',
                                       inverse='_inverse_multi_qty_delivered',
                                       store=True,
                                       digits='Product Unit of Measure',
                                       default=0.0)
    multi_qty_delivered_manual = fields.Float('DeliveredManually',
                                              copy=False,
                                              digits='Product Unit of Measure',
                                              default=0.0)
    multi_qty_to_invoice = fields.Float(compute='_get_to_multi_invoice_qty',
                                        string='Invoice Qty',
                                        store=True,
                                        digits='Product Unit of Measure')
    multi_qty_invoiced = fields.Float(compute='_compute_multi_qty_invoiced',
                                      string='Invoiced Qty',
                                      store=True,
                                      digits='Product Unit of Measure')
    price_unit = fields.Float(compute='compute_multi_price_unit',
                              inverse='set_multi_price_unit',
                              store=True,
                              digits='Multi Product Price')
    multi_price_unit = fields.Float('Multi Price Unit', digits='Product Price', copy=False)
    multi_uom_discount = fields.Float('Discount')
    multi_uom_line_ids = fields.Many2many('multi.uom.line', compute='compute_multi_uom_line_ids')
    discount_amt = fields.Float(compute='_compute_multi_uom_discount',
                                inverse='_set_multi_uom_discount',
                                store=True,
                                digits='Multi UoM Discount')

    @api.depends('multi_uom_line_id', 'multi_uom_discount')
    def _compute_multi_uom_discount(self):
        for line in self:
            if line.multi_uom_line_id:
                line.discount_amt = line.multi_uom_discount / line.multi_uom_line_id.ratio
            else:
                line.discount_amt = line.multi_uom_discount

    def _set_multi_uom_discount(self):
        for line in self:
            if line.multi_uom_line_id:
                line.multi_uom_discount = line.discount_amt * line.multi_uom_line_id.ratio
            else:
                line.multi_uom_discount = line.discount_amt

    @api.depends('product_id')
    def compute_multi_uom_line_ids(self):
        for rec in self:
            rec.multi_uom_line_ids = rec.product_id.multi_uom_line_ids.ids

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        res = super(SaleOrderLine, self).product_uom_change()
        if self.multi_price_unit:
            self.compute_multi_price_unit()
        return res

    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        line = self.product_id.multi_uom_line_ids.filtered(lambda l: l.is_default_uom == True)
        self.multi_uom_line_id = line.id
        return res

    @api.onchange('product_uom', 'product_uom_qty', 'multi_uom_line_id')
    def product_uom_change(self):
        res = super().product_uom_change()
        return res

    def _get_display_price(self, product):
        pricelist_mode = self.env['ir.config_parameter'].get_param('product.product_pricelist_setting')
        if self.multi_uom_line_id and pricelist_mode == 'uom':
            uom_price = self.order_id.pricelist_id._get_pricelist_uom_price(self.product_id, self.multi_uom_line_id,
                                                                            self.multi_uom_qty)
            self.multi_price_unit = uom_price
            price = uom_price / self.multi_uom_line_id.ratio
        else:
            price = super(SaleOrderLine, self)._get_display_price(product)
            if self.multi_uom_line_id:
                self.multi_price_unit = price * self.multi_uom_line_id.ratio
        return price

    @api.depends('multi_uom_line_id', 'multi_uom_qty')
    def compute_product_uom_qty(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.product_uom_qty = rec.multi_uom_qty * rec.multi_uom_line_id.ratio
            else:
                rec.product_uom_qty = 0

    def set_multi_uom_qty(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.multi_uom_qty = rec.product_uom_qty / rec.multi_uom_line_id.ratio

    @api.depends('multi_uom_line_id', 'qty_invoiced')
    def _compute_multi_qty_invoiced(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.multi_qty_invoiced = rec.qty_invoiced / rec.multi_uom_line_id.ratio
            else:
                rec.multi_qty_invoiced = 0

    @api.depends('multi_uom_line_id', 'qty_to_invoice')
    def _get_to_multi_invoice_qty(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.multi_qty_to_invoice = rec.qty_to_invoice / rec.multi_uom_line_id.ratio
            else:
                rec.multi_qty_to_invoice = 0

    @api.depends('multi_uom_line_id', 'qty_delivered')
    def _compute_multi_qty_delivered(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.multi_qty_delivered = rec.qty_delivered / rec.multi_uom_line_id.ratio
            else:
                rec.multi_qty_delivered = 0

    @api.depends('multi_uom_line_id', 'multi_qty_delivered')
    def _inverse_multi_qty_delivered(self):
        for rec in self:
            rec.qty_delivered = rec.multi_qty_delivered * rec.multi_uom_line_id.ratio

    @api.depends('multi_uom_line_id', 'multi_qty_delivered_manual')
    def compute_manual_delivered_qty(self):
        for rec in self:
            rec.qty_delivered_manual = rec.multi_qty_delivered_manual * rec.multi_uom_line_id.ratio

    def set_multi_qty_delivered_manual(self):
        for rec in self:
            rec.multi_qty_delivered_manual = rec.qty_delivered_manual * rec.multi_uom_line_id.ratio

    @api.depends('multi_uom_line_id', 'multi_price_unit')
    def compute_multi_price_unit(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.price_unit = rec.multi_price_unit / rec.multi_uom_line_id.ratio
            else:
                rec.price_unit = rec.multi_price_unit

    def set_multi_price_unit(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.multi_price_unit = rec.price_unit * rec.multi_uom_line_id.ratio
            else:
                rec.multi_price_unit = rec.price_unit

    def _prepare_procurement_values(self, group_id=False):
        values = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        values.update({
            'multi_uom_line_id': self.multi_uom_line_id.id,
        })
        return values

    def _prepare_invoice_line(self, **optional_values):
        values = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        values['multi_uom_discount'] = self.multi_uom_discount
        values['multi_uom_line_id'] = self.multi_uom_line_id.id
        return values


class SaleOrderTemplateLine(models.Model):
    _inherit = 'sale.order.template.line'

    product_uom_qty = fields.Float(compute='compute_product_uom_qty',
                                   inverse='set_multi_uom_qty',
                                   store=True,
                                   readonly=False)

    multi_uom_line_id = fields.Many2one('multi.uom.line', 'UoM')
    uom_ratio_remark = fields.Char(string='Ratio Remark', related='multi_uom_line_id.remark')
    multi_uom_qty = fields.Float('UOM Qty',
                                 digits='Product Unit of Measure',
                                 default=1.0)

    multi_uom_line_ids = fields.Many2many('multi.uom.line', compute='compute_multi_uom_line_ids')

    @api.depends('multi_uom_line_id', 'multi_uom_qty')
    def compute_product_uom_qty(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.product_uom_qty = rec.multi_uom_qty * rec.multi_uom_line_id.ratio
            else:
                rec.product_uom_qty = 0

    def set_multi_uom_qty(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.multi_uom_qty = rec.product_uom_qty / rec.multi_uom_line_id.ratio

    @api.depends('product_id')
    def compute_multi_uom_line_ids(self):
        for rec in self:
            rec.multi_uom_line_ids = []
            if rec.product_id.multi_uom_line_ids:
                rec.multi_uom_line_ids = rec.product_id.multi_uom_line_ids.ids

    @api.onchange('product_id')
    def product_id_change(self):
        for rec in self:
            if rec.product_id:
                line = rec.product_id.multi_uom_line_ids.filtered(lambda l: l.is_default_uom == True)
                rec.multi_uom_line_id = line


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('sale_order_template_id')
    def onchange_sale_order_template_id(self):
        res = super(SaleOrder, self).onchange_sale_order_template_id()
        if self.sale_order_template_id:
            template = self.sale_order_template_id.with_context(lang=self.partner_id.lang)
            order_lines = [(5, 0, 0)]
            for line in template.sale_order_template_line_ids:
                data = self._compute_line_data_for_template_change(line)

                if line.product_id:
                    price = line.product_id.lst_price
                    discount = 0

                    if self.pricelist_id:
                        pricelist_price = self.pricelist_id.with_context(uom=line.product_uom_id.id).get_product_price(
                            line.product_id, 1, False)

                        if self.pricelist_id.discount_policy == 'without_discount' and price:
                            discount = max(0, (price - pricelist_price) * 100 / price)
                        else:
                            price = pricelist_price

                    data.update({
                        'price_unit': price,
                        'multi_price_unit':price,
                        'discount': discount,
                        'multi_uom_qty': line.multi_uom_qty,
                        'product_id': line.product_id.id,
                        'product_uom': line.product_uom_id.id,
                        'multi_uom_line_id':line.multi_uom_line_id.id,
                        'customer_lead': self._get_customer_lead(line.product_id.product_tmpl_id),
                    })
                order_lines.append((0, 0, data))

            self.order_line = order_lines
            self.order_line._compute_tax_id()

            # then, process the list of optional products from the template
            option_lines = [(5, 0, 0)]
            for option in template.sale_order_template_option_ids:
                data = self._compute_option_data_for_template_change(option)
                option_lines.append((0, 0, data))

            self.sale_order_option_ids = option_lines

            if template.number_of_days > 0:
                self.validity_date = fields.Date.context_today(self) + timedelta(template.number_of_days)

            self.require_signature = template.require_signature
            self.require_payment = template.require_payment

            if not is_html_empty(template.note):
                self.note = template.note
        return res
