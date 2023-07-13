from odoo import api, models, fields


class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    quantity = fields.Float(compute='compute_multi_uom_qty', inverse='set_uom_qty', store=True, readonly=False)
    price_unit = fields.Float('Price Unit',
                              compute='compute_multi_price_unit',
                              inverse='set_multi_price_unit',
                              store=True,
                              digits='Multi Product Price')
    multi_price_unit = fields.Float('PriceUnit')
    multi_uom_discount = fields.Float('Discount')
    discount = fields.Float(compute='_compute_multi_uom_discount',
                            inverse='_set_multi_uom_discount',
                            store=True,
                            digits='Multi UoM Discount')
    multi_uom_qty = fields.Float(string='Qty',
                                 default=1.0,
                                 digits='Product Unit of Measure',
                                 help="The optional quantity expressed by this line, eg: number of product sold. "
                                      "The quantity is not a legal requirement but is very useful for some reports.")
    multi_uom_line_id = fields.Many2one('multi.uom.line', 'UoM')
    uom_ratio_remark = fields.Char(string='Ratio Remark', related='multi_uom_line_id.remark')
    multi_uom_line_ids = fields.Many2many('multi.uom.line', compute='compute_multi_uom_line_ids')

    @api.depends('multi_uom_line_id', 'multi_uom_discount', 'discount_type')
    def _compute_multi_uom_discount(self):
        for line in self:

            if line.multi_uom_line_id and line.discount_type == 'fixed':
                line.discount = line.multi_uom_discount / line.multi_uom_line_id.ratio
            else:
                line.discount = line.multi_uom_discount

    def _set_multi_uom_discount(self):
        for line in self:
            if line.multi_uom_line_id:
                line.multi_uom_discount = line.discount * line.multi_uom_line_id.ratio
            else:
                line.multi_uom_discount = line.discount

    @api.depends('multi_uom_line_id', 'multi_price_unit')
    def compute_multi_price_unit(self):
        for rec in self:
            if rec.multi_uom_line_id:

                rec.price_unit = (rec.multi_price_unit / rec.multi_uom_line_id.ratio)

            else:
                rec.price_unit = rec.multi_price_unit

    def set_multi_price_unit(self):
        for rec in self:
            rec.multi_price_unit = rec.price_unit *rec.multi_uom_line_id.ratio


    @api.depends('product_id')
    def compute_multi_uom_line_ids(self):
        for rec in self:
            rec.multi_uom_line_ids = rec.product_id.multi_uom_line_ids.ids

    @api.onchange('product_id')
    def auto_complete_multi_uom(self):
        line = self.product_id.multi_uom_line_ids.filtered(lambda l: l.is_default_uom == True)
        self.multi_uom_line_id = line.id

    @api.depends('multi_uom_line_id', 'multi_uom_qty')
    def compute_multi_uom_qty(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.quantity = rec.multi_uom_qty * rec.multi_uom_line_id.ratio

            else:
                rec.quantity = 0

    def set_uom_qty(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.multi_uom_qty = rec.quantity / rec.multi_uom_line_id.ratio


    def _copy_data_extend_business_fields(self, values):
        super(AccountMoveLine, self)._copy_data_extend_business_fields(values)
        values['multi_uom_qty'] = self.multi_uom_qty
        values['multi_price_unit'] = self.multi_price_unit
        values['multi_uom_line_id'] = self.multi_uom_line_id.id
