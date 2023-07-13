from odoo import api, models, fields, _
from collections import defaultdict

from odoo.tools import float_round, float_is_zero


class StockMove(models.Model):
    _inherit = 'stock.move'

    product_uom_qty = fields.Float(string='QTY', compute='convert_to_product_uom_qty',
                                   inverse='convert_to_multi_uom_qty', store=True)
    multi_uom_qty = fields.Float('Demand Qty', digits='Product Unit of Measure', )
    multi_uom_line_id = fields.Many2one('multi.uom.line', 'Multi UOM Line')
    uom_ratio_remark = fields.Char(string='Ratio Remark', related='multi_uom_line_id.remark')
    multi_availability = fields.Float('Forecasted Qty',
                                      compute='_compute_multi_availability',
                                      readonly=True,
                                      help='Quantity in stock that can still be reserved for this move')
    multi_forecast_availability = fields.Float('ForecastAvailability',
                                               compute='_compute_multi_forecast_availability',
                                               digits='Product Unit of Measure',
                                               compute_sudo=True)
    multi_reserved_availability = fields.Float('QuantityReserved',
                                               compute='_compute_multi_reserved_availability',
                                               digits='Product Unit of Measure',
                                               readonly=True,
                                               help='Quantity that has already been reserved for this move')
    multi_quantity_done = fields.Float('Qty Done',
                                       compute='_multi_uom_quantity_done_compute',
                                       digits='Product Unit of Measure',
                                       inverse='_multi_uom_quantity_done_set')
    multi_uom_line_ids = fields.Many2many('multi.uom.line', compute='compute_multi_uom_line_ids')
    multi_should_consume_qty = fields.Float('Quantity To Consume', default=0.0,
                                            compute='_compute_multi_should_consume_qty',
                                            digits='Product Unit of Measure')
    real_product_qty = fields.Float(string='Real Product Qty')

    standard_qty = fields.Float(string='Standard QTY',digits='Product Unit of Measure')
    difference_qty = fields.Float(string='Difference QTY', compute='_get_difference_qty',digits='Product Unit of Measure')

    @api.depends('standard_qty', 'multi_quantity_done')
    def _get_difference_qty(self):
        self.difference_qty = 0
        for rec in self:
            if rec.standard_qty or rec.multi_quantity_done:
                rec.difference_qty = rec.multi_quantity_done - rec.standard_qty

    def _should_bypass_set_qty_producing(self):

        if self.state in ('done', 'cancel'):
            return True
        # Do not update extra product quantities
        if self.multi_uom_line_id:
            if float_is_zero(self.multi_uom_qty, precision_rounding=self.multi_uom_line_id.uom_id.rounding):
                return True
        if self.has_tracking != 'none' or self.state == 'done':
            return True

        return False

    @api.depends('product_id')
    def compute_multi_uom_line_ids(self):
        for rec in self:
            rec.multi_uom_line_ids = rec.product_id.multi_uom_line_ids.ids

    @api.model
    def create(self, values):
        product = self.env['product.product'].browse(values.get('product_id', False))
        if product and 'multi_uom_line_id' not in values:
            values['multi_uom_line_id'] = product.multi_uom_line_ids.filtered(
                lambda l: l.uom_id.id == product.uom_id.id
            ).id
        return super(StockMove, self).create(values)

    @api.onchange('product_id')
    def onchange_multi_uom_product_id(self):
        line = self.product_id.multi_uom_line_ids.filtered(lambda l: l.is_default_uom == True)
        self.multi_uom_line_id = line.id

    @api.depends('multi_uom_line_id', 'multi_uom_qty')
    def convert_to_product_uom_qty(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.product_uom_qty = rec.multi_uom_qty * rec.multi_uom_line_id.ratio
            else:
                print('222222222222222222222222222222222222222222222222222222')
                rec.product_uom_qty = 0

    @api.depends('should_consume_qty', 'multi_uom_line_id')
    def _compute_multi_should_consume_qty(self):
        for rec in self:
            if rec.should_consume_qty and rec.multi_uom_line_id:
                rec.multi_should_consume_qty = rec.should_consume_qty / rec.multi_uom_line_id.ratio
            else:
                rec.multi_should_consume_qty = 0

    def convert_to_multi_uom_qty(self):
        for rec in self:
            if rec.ws_req_line_id:
                rec.convert_to_product_uom_qty()
            if rec.multi_uom_line_id:

                if rec.bom_line_id:
                    rec.multi_uom_qty = rec.product_uom_qty / rec.multi_uom_line_id.ratio
                else:
                    rec.multi_uom_qty = rec.product_uom_qty / rec.multi_uom_line_id.ratio


    @api.depends('multi_uom_line_id', 'availability')
    def _compute_multi_availability(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.multi_availability = rec.availability / rec.multi_uom_line_id.ratio
            else:
                rec.multi_availability = 0

    def _compute_multi_forecast_availability(self):
        for rec in self:
            if rec.multi_uom_line_id:
                qty = rec.get_multi_forecast_availability()
                rec.multi_forecast_availability = qty / rec.multi_uom_line_id.ratio
            else:
                rec.multi_forecast_availability = 0

    @api.depends('multi_uom_line_id', 'reserved_availability')
    def _compute_multi_reserved_availability(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.multi_reserved_availability = rec.reserved_availability / rec.multi_uom_line_id.ratio
            else:
                rec.multi_reserved_availability = 0

    @api.depends('multi_uom_line_id', 'multi_quantity_done')
    def _multi_uom_quantity_done_compute(self):
        for rec in self:
            if rec.multi_uom_line_id:
                if rec.bom_line_id:
                    print('22222222222222222222222222222222222222222222222211111111111111111111')
                    rec.multi_quantity_done = rec.quantity_done /rec.multi_uom_line_id.ratio

            else:
                rec.multi_quantity_done = 0

    def _multi_uom_quantity_done_set(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.quantity_done = rec.multi_quantity_done * rec.multi_uom_line_id.ratio

    def get_multi_forecast_availability(self):
        """ Compute forecasted information of the related product by warehouse."""
        self.forecast_availability = False
        self.forecast_expected_date = False

        # Prefetch product info to avoid fetching all product fields
        self.product_id.read(['type', 'uom_id'], load=False)

        not_product_moves = self.filtered(lambda move: move.product_id.type != 'product')
        for move in not_product_moves:
            move.forecast_availability = move.product_qty

        product_moves = (self - not_product_moves)

        outgoing_unreserved_moves_per_warehouse = defaultdict(set)
        now = fields.Datetime.now()

        def key_virtual_available(move, incoming=False):
            warehouse_id = move.location_dest_id.warehouse_id.id if incoming else move.location_id.warehouse_id.id
            return warehouse_id, max(move.date, now)

        # Prefetch efficiently virtual_available for _consuming_picking_types draft move.
        prefetch_virtual_available = defaultdict(set)
        virtual_available_dict = {}
        for move in product_moves:
            if move.picking_type_id.code in self._consuming_picking_types() and move.state == 'draft':
                prefetch_virtual_available[key_virtual_available(move)].add(move.product_id.id)
            elif move.picking_type_id.code == 'incoming':
                prefetch_virtual_available[key_virtual_available(move, incoming=True)].add(move.product_id.id)
        for key_context, product_ids in prefetch_virtual_available.items():
            read_res = self.env['product.product'].browse(product_ids).with_context(warehouse=key_context[0],
                                                                                    to_date=key_context[1]).read(
                ['virtual_available'])
            virtual_available_dict[key_context] = {res['id']: res['virtual_available'] for res in read_res}

        for move in product_moves:
            if move.picking_type_id.code in self._consuming_picking_types():
                if move.state == 'assigned':
                    move.forecast_availability = move.product_uom._compute_quantity(
                        move.reserved_availability, move.product_id.uom_id, rounding_method='HALF-UP')
                elif move.state == 'draft':
                    # for move _consuming_picking_types and in draft -> the forecast_availability > 0 if in stock
                    move.forecast_availability = virtual_available_dict[key_virtual_available(move)][
                                                     move.product_id.id] - move.product_qty
                elif move.state in ('waiting', 'confirmed', 'partially_available'):
                    outgoing_unreserved_moves_per_warehouse[move.location_id.warehouse_id].add(move.id)
            elif move.picking_type_id.code == 'incoming':
                forecast_availability = virtual_available_dict[key_virtual_available(move, incoming=True)][
                    move.product_id.id]
                if move.state == 'draft':
                    forecast_availability += move.product_qty
                move.forecast_availability = forecast_availability

        for warehouse, moves_ids in outgoing_unreserved_moves_per_warehouse.items():
            if not warehouse:  # No prediction possible if no warehouse.
                continue
            moves = self.browse(moves_ids)
            forecast_info = moves._get_forecast_availability_outgoing(warehouse)
            for move in moves:
                move.forecast_availability, move.forecast_expected_date = forecast_info[move]
        return move.forecast_availability

    def _prepare_procurement_values(self):
        values = super(StockMove, self)._prepare_procurement_values()
        values['multi_uom_line_id'] = self.multi_uom_line_id.id
        return values
