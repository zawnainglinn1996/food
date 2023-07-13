from odoo import api, models, fields
from odoo.exceptions import UserError


class StockWarehouseOrderpoint(models.Model):
    _inherit = "stock.warehouse.orderpoint"

    product_min_qty = fields.Float(compute='_compute_multi_product_min_qty',
                                   inverse='_set_multi_product_min_qty', store=True)
    product_max_qty = fields.Float(compute='_compute_multi_product_max_qty',
                                   inverse='_set_multi_product_max_qty', store=True)
    qty_multiple = fields.Float(compute='_compute_multi_qty_multiple',
                                inverse='_set_multi_qty_multiple', store=True)

    multi_product_min_qty = fields.Float('Multi Min Qty',
                                         digits='Product Unit of Measure',
                                         required=True,
                                         default=0.0,
                                         help="When the virtual stock equals to or goes below the Min Quantity "
                                              "specified for this field, Odoo generates a procurement to bring the "
                                              "forecasted quantity to the Max Quantity.")
    multi_product_max_qty = fields.Float('Multi Max Qty',
                                         digits='Product Unit of Measure',
                                         required=True,
                                         default=0.0,
                                         help="When the virtual stock goes below the Min Quantity, Odoo generates "
                                              "a procurement to bring the forecasted quantity to the Quantity specified"
                                              "as Max Quantity.")
    multi_qty_multiple = fields.Float('Multiple Qty',
                                      digits='Product Unit of Measure',
                                      default=1,
                                      required=True,
                                      help="The procurement quantity will be rounded up to this multiple.  "
                                           "If it is 0, the exact quantity will be used.")
    multi_qty_on_hand = fields.Float('On Hand Qty', readonly=True, compute='_compute_multi_qty')
    multi_qty_forecast = fields.Float('Forecast Qty', readonly=True, compute='_compute_multi_qty')
    multi_qty_to_order = fields.Float('To Order Qty', compute='_compute_multi_qty_to_order', store=True, readonly=False)
    multi_uom_line_id = fields.Many2one('multi.uom.line', 'UoM')
    multi_uom_line_ids = fields.Many2many('multi.uom.line', compute='compute_multi_uom_line_ids')

    @api.model
    def create(self, values):
        product = self.env['product.product'].browse(values.get('product_id', False))

        if product and "multi_uom_line_id" in values:

            if product.multi_uom_line_ids:
                uom_id = values['multi_uom_line_id']
                uom_line_id = self.env['multi.uom.line'].browse(uom_id)
                multi_uom_line_id = product.multi_uom_line_ids.filtered(lambda l: l.uom_id.id == uom_line_id.uom_id.id)
                product_min_qty = values['multi_product_min_qty'] * multi_uom_line_id.ratio
                product_max_qty = values['multi_product_max_qty'] * multi_uom_line_id.ratio
                values.update({
                    'product_min_qty': product_min_qty,
                    'product_max_qty': product_max_qty,
                    'multi_uom_line_id': multi_uom_line_id.id
                })

            else:
                raise UserError('!!!MUOM Lines Missing in Product !!!')

        return super(StockWarehouseOrderpoint, self).create(values)

    @api.depends('product_id')
    def compute_multi_uom_line_ids(self):
        for rec in self:
            rec.multi_uom_line_ids = rec.product_id.multi_uom_line_ids.ids

    @api.depends('multi_uom_line_id', 'multi_product_min_qty')
    def _compute_multi_product_min_qty(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.product_min_qty = rec.multi_product_min_qty * rec.multi_uom_line_id.ratio
            else:
                rec.product_min_qty = rec.multi_product_min_qty

    def _set_multi_product_min_qty(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.multi_product_min_qty = (rec.product_min_qty / rec.multi_uom_line_id.ratio)
            else:
                rec.multi_product_min_qty = rec.product_min_qty

    @api.depends('multi_uom_line_id', 'multi_product_max_qty')
    def _compute_multi_product_max_qty(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.product_max_qty = rec.multi_product_max_qty * rec.multi_uom_line_id.ratio
            else:
                rec.product_max_qty = rec.multi_product_max_qty

    def _set_multi_product_max_qty(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.multi_product_max_qty = (rec.product_max_qty / rec.multi_uom_line_id.ratio)
            else:
                rec.multi_product_max_qty = rec.product_max_qty

    @api.depends('multi_uom_line_id', 'multi_qty_multiple')
    def _compute_multi_qty_multiple(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.qty_multiple = rec.multi_qty_multiple * rec.multi_uom_line_id.ratio
            else:
                rec.qty_multiple = rec.multi_qty_multiple

    def _set_multi_qty_multiple(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.multi_qty_multiple = (rec.qty_multiple / rec.multi_uom_line_id.ratio)
            else:
                rec.multi_qty_multiple = rec.qty_multiple

    def _compute_multi_qty(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.multi_qty_on_hand = rec.qty_on_hand / rec.multi_uom_line_id.ratio
                rec.multi_qty_forecast = rec.qty_forecast / rec.multi_uom_line_id.ratio
            else:
                rec.multi_qty_on_hand = rec.qty_on_hand
                rec.multi_qty_forecast = rec.qty_forecast

    @api.depends('multi_uom_line_id', 'qty_to_order')
    def _compute_multi_qty_to_order(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.multi_qty_to_order = rec.qty_to_order / rec.multi_uom_line_id.ratio
            else:
                rec.multi_qty_to_order = rec.qty_to_order

    def _prepare_procurement_values(self, date=False, group=False):
        values = super(StockWarehouseOrderpoint, self)._prepare_procurement_values(date, group)
        values['multi_uom_line_id'] = self.multi_uom_line_id.id
        return values
