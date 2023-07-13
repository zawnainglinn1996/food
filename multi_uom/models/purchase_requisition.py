from odoo import api, models, fields


class PurchaseRequisitionLine(models.Model):

    _inherit = "purchase.requisition.line"

    multi_uom_line_id = fields.Many2one('multi.uom.line', 'UoM')
    product_tmpl_id = fields.Many2one('product.template', string='Product Template', related='product_id.product_tmpl_id')
    product_qty = fields.Float(string='Quantity',
                               digits='Product Unit of Measure',
                               compute='_compute_product_qty',
                               inverse='_set_product_qty',
                               store=True)
    price_unit = fields.Float(string='Unit Price', digits='Product Price',
                              compute='_compute_price_unit',
                              inverse='_set_price_unit',
                              store=True)
    multi_product_qty = fields.Float(string='Multi Quantity', digits='Product Unit of Measure')
    multi_price_unit = fields.Float(string='Multi Unit Price', digits='Product Price')
    multi_qty_ordered = fields.Float(compute='_compute_multi_ordered_qty', string='Multi Ordered Quantities')

    @api.model
    def create(self, values):
        if 'multi_uom_line_id' not in values:
            product = self.env['product.product'].browse(values['product_id'])
            multi_uom_line = product.multi_uom_line_ids.filtered(lambda l: l.uom_id.id == product.uom_id.id)
            values['multi_uom_line_id'] = multi_uom_line.id
        return super(PurchaseRequisitionLine, self).create(values)

    @api.depends('multi_uom_line_id', 'multi_product_qty')
    def _compute_product_qty(self):
        for line in self:
            if line.multi_uom_line_id:
                line.product_qty = line.multi_product_qty * line.multi_uom_line_id.ratio
            else:
                line.product_qty = line.multi_product_qty

    def _set_product_qty(self):
        for line in self:
            if line.multi_uom_line_id:
                line.multi_product_qty = line.product_qty / line.multi_uom_line_id.ratio
            else:
                line.multi_product_qty = line.product_qty

    @api.depends('multi_uom_line_id', 'multi_price_unit')
    def _compute_price_unit(self):
        for line in self:
            if line.multi_uom_line_id:
                line.price_unit = line.multi_price_unit / line.multi_uom_line_id.ratio
            else:
                line.price_unit = line.multi_price_unit

    def _set_price_unit(self):
        for line in self:
            if line.multi_uom_line_id:
                line.multi_price_unit = line.price_unit * line.multi_uom_line_id.ratio
            else:
                line.multi_price_unit = line.price_unit

    @api.depends('qty_ordered')
    def _compute_multi_ordered_qty(self):
        for line in self:
            if line.multi_uom_line_id:
                line.multi_qty_ordered = line.qty_ordered / line.multi_uom_line_id.ratio
            else:
                line.multi_qty_ordered = line.qty_ordered

    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = super(PurchaseRequisitionLine, self)._onchange_product_id()
        product = self.product_id
        self.multi_uom_line_id = product.multi_uom_line_ids.filtered(lambda l: l.is_default_uom == True)
        return res

    def _prepare_purchase_order_line(self, name, product_qty=0.0, price_unit=0.0, taxes_ids=False):
        values = super(PurchaseRequisitionLine, self)._prepare_purchase_order_line(name,
                                                                                   product_qty,
                                                                                   price_unit,
                                                                                   taxes_ids)
        values['multi_uom_line_id'] = self.multi_uom_line_id.id
        values['purchase_uom_qty'] = self.multi_product_qty
        values['multi_price_unit'] = self.multi_price_unit
        return values
