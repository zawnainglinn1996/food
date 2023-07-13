from dateutil.relativedelta import relativedelta

from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tools import float_round
from odoo.tools import float_compare, float_round, float_is_zero, format_datetime


class MrpProduction(models.Model):
    _inherit = "mrp.production"
    multi_uom_line_ids = fields.Many2many('multi.uom.line', compute='compute_multi_uom_line_ids')
    multi_uom_line_id = fields.Many2one('multi.uom.line', 'Multi UOM')
    product_multi_uom_qty = fields.Float('Multi Request Qty', default=1.0,
                                         digits='Product Unit of Measure', readonly=False, required=True, tracking=True,
                                         states={'draft': [('readonly', False)]})
    multi_qty_producing = fields.Float(string="Multi Quantity Producing", copy=False)

    product_qty = fields.Float(compute='compute_multi_uom_line_qty',
                               inverse='set_multi_uom_line_qty',
                               store=True, readonly=False)

    qty_producing = fields.Float(compute='compute_multi_uom_producing_qty',
                                 inverse='set_multi_uom_producing_qty',
                                 store=True, readonly=False)

    @api.depends('multi_uom_line_id', 'multi_qty_producing')
    def compute_multi_uom_producing_qty(self):
        for rec in self:
            rec.qty_producing = rec.multi_uom_line_id.ratio * rec.multi_qty_producing

    def set_multi_uom_producing_qty(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.multi_qty_producing = rec.qty_producing / rec.multi_uom_line_id.ratio
            else:
                rec.multi_qty_producing = rec.qty_producing

    @api.depends('product_id', 'multi_uom_line_id', 'product_multi_uom_qty')
    def compute_multi_uom_line_qty(self):
        for rec in self:
            rec.product_qty = rec.multi_uom_line_id.ratio * rec.product_multi_uom_qty

    def set_multi_uom_line_qty(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.product_multi_uom_qty = rec.product_qty / rec.multi_uom_line_id.ratio
            else:
                rec.product_multi_uom_qty = rec.product_qty

    @api.onchange('product_id', 'picking_type_id', 'company_id', 'bom_id')
    def _onchange_multi_uom_qty(self):
        """ Finds UoM of changed product. """
        if self.bom_id:
            if not self.bom_id.multi_uom_line_id:
                raise UserError(
                    _("Selected  Product Name - (%s) is missing UOM ." % self.product_id.name))
            self.multi_uom_line_id = self.bom_id.multi_uom_line_id.id

    @api.depends('product_id')
    def compute_multi_uom_line_ids(self):
        for rec in self:
            rec.multi_uom_line_ids = []
            if rec.product_id.multi_uom_line_ids:
                rec.multi_uom_line_ids = rec.product_id.multi_uom_line_ids.ids

    def _get_move_finished_values(self, product_id, product_uom_qty, product_uom, multi_uom_qty, multi_uom_line_id,
                                  operation_id=False,
                                  byproduct_id=False, cost_share=0):
        group_orders = self.procurement_group_id.mrp_production_ids
        move_dest_ids = self.move_dest_ids
        if len(group_orders) > 1:
            move_dest_ids |= group_orders[0].move_finished_ids.filtered(
                lambda m: m.product_id == self.product_id).move_dest_ids
        date_planned_finished = self.date_planned_start + relativedelta(days=self.product_id.produce_delay)
        date_planned_finished = date_planned_finished + relativedelta(days=self.company_id.manufacturing_lead)
        if date_planned_finished == self.date_planned_start:
            date_planned_finished = date_planned_finished + relativedelta(hours=1)
        print(
            '---------------------------------------------------------------------------------++++++++++++++++++++++++')
        return {
            'product_id': product_id,
            'product_uom_qty': product_uom_qty,
            'product_uom': product_uom,
            'operation_id': operation_id,
            'byproduct_id': byproduct_id,
            'multi_uom_qty': multi_uom_qty,
            'multi_uom_line_id': multi_uom_line_id,
            'name': self.name,
            'date': date_planned_finished,
            'date_deadline': self.date_deadline,
            'picking_type_id': self.picking_type_id.id,
            'location_id': self.product_id.with_company(self.company_id).property_stock_production.id,
            'location_dest_id': self.location_dest_id.id,
            'company_id': self.company_id.id,
            'production_id': self.id,
            'warehouse_id': self.location_dest_id.warehouse_id.id,
            'origin': self.name,
            'group_id': self.procurement_group_id.id,
            'propagate_cancel': self.propagate_cancel,
            'move_dest_ids': [(4, x.id) for x in self.move_dest_ids if not byproduct_id],
            'cost_share': cost_share,
        }

    def _get_moves_finished_values(self):
        moves = []
        for production in self:
            if production.product_id in production.bom_id.byproduct_ids.mapped('product_id'):
                raise UserError(
                    _("You cannot have %s  as the finished product and in the Byproducts", self.product_id.name))

            multi_uom_qty = production.product_multi_uom_qty if production.product_multi_uom_qty else 0
            multi_uom_line_id = production.multi_uom_line_id.id if production.multi_uom_line_id else 0

            moves.append(production._get_move_finished_values(production.product_id.id, production.product_qty,
                                                              production.product_uom_id.id, multi_uom_qty,
                                                              multi_uom_line_id, ))
            for byproduct in production.bom_id.byproduct_ids:
                if byproduct._skip_byproduct_line(production.product_id):
                    continue
                product_uom_factor = production.product_uom_id._compute_quantity(production.product_qty,
                                                                                 production.bom_id.product_uom_id)
                qty = byproduct.product_qty * (product_uom_factor / production.bom_id.product_qty)
                moves.append(production._get_move_finished_values(
                    byproduct.product_id.id, qty, byproduct.product_uom_id.id,
                    byproduct.operation_id.id, byproduct.id, byproduct.cost_share))
        return moves

    def _get_moves_raw_values(self):
        moves = []
        for production in self:
            if not production.bom_id:
                continue
            factor = production.product_uom_id._compute_quantity(production.product_multi_uom_qty,
                                                                 production.bom_id.product_uom_id) / production.bom_id.product_qty
            boms, lines = production.bom_id.explode(production.product_id, factor,
                                                    picking_type=production.bom_id.picking_type_id)
            for bom_line, line_data in lines:
                if bom_line.child_bom_id and bom_line.child_bom_id.type == 'phantom' or \
                        bom_line.product_id.type not in ['product', 'consu']:
                    continue
                operation = bom_line.operation_id.id or line_data['parent_line'] and line_data[
                    'parent_line'].operation_id.id

                moves.append(production._get_move_raw_values(
                    bom_line.product_id,
                    line_data['qty'],
                    bom_line.product_uom_id,
                    operation,
                    bom_line
                ))
        return moves

    def _get_move_raw_values(self, product_id, product_uom_qty, product_uom,
                             operation_id=False, bom_line=False):
        source_location = self.location_src_id
        origin = self.name
        if self.orderpoint_id and self.origin:
            origin = self.origin.replace(
                '%s - ' % (self.orderpoint_id.display_name), '')
            origin = '%s,%s' % (origin, self.name)
        data = {
            'sequence': bom_line.sequence if bom_line else 10,
            'name': self.name,
            'date': self.date_planned_start,
            'date_deadline': self.date_planned_start,
            'bom_line_id': bom_line.id if bom_line else False,
            'picking_type_id': self.picking_type_id.id,
            'product_id': product_id.id,
            'product_uom_qty': product_uom_qty,
            'multi_uom_qty': product_uom_qty,
            'product_uom': product_uom.id,
            'multi_uom_line_id': bom_line.multi_uom_line_id.id if bom_line.multi_uom_line_id else False,
            'real_product_qty': bom_line.real_product_qty if bom_line.real_product_qty else 0.0,
            'location_id': source_location.id,
            'location_dest_id': self.product_id.with_company(self.company_id).property_stock_production.id,
            'raw_material_production_id': self.id,
            'company_id': self.company_id.id,
            'operation_id': operation_id,
            'price_unit': product_id.standard_price,
            'procure_method': 'make_to_stock',
            'origin': origin,
            'state': 'draft',
            'warehouse_id': source_location.warehouse_id.id,
            'group_id': self.procurement_group_id.id,
            'propagate_cancel': self.propagate_cancel,
        }
        return data

    # def _get_move_finished_values(self, product_id, product_uom_qty, product_uom, operation_id=False, byproduct_id=False, cost_share=0):
    #     group_orders = self.procurement_group_id.mrp_production_ids
    #     move_dest_ids = self.move_dest_ids
    #     if len(group_orders) > 1:
    #         move_dest_ids |= group_orders[0].move_finished_ids.filtered(lambda m: m.product_id == self.product_id).move_dest_ids
    #     date_planned_finished = self.date_planned_start + relativedelta(days=self.product_id.produce_delay)
    #     date_planned_finished = date_planned_finished + relativedelta(days=self.company_id.manufacturing_lead)
    #     if date_planned_finished == self.date_planned_start:
    #         date_planned_finished = date_planned_finished + relativedelta(hours=1)
    #     return {
    #         'product_id': product_id,
    #         'product_uom_qty': product_uom_qty,
    #         'product_uom': product_uom,
    #         'operation_id': operation_id,
    #         'byproduct_id': byproduct_id,
    #         'multi_uom_line_id':self.multi_uom_line_id.id,
    #         'name': self.name,
    #         'date': date_planned_finished,
    #         'date_deadline': self.date_deadline,
    #         'picking_type_id': self.picking_type_id.id,
    #         'location_id': self.product_id.with_company(self.company_id).property_stock_production.id,
    #         'location_dest_id': self.location_dest_id.id,
    #         'company_id': self.company_id.id,
    #         'production_id': self.id,
    #         'warehouse_id': self.location_dest_id.warehouse_id.id,
    #         'origin': self.name,
    #         'group_id': self.procurement_group_id.id,
    #         'propagate_cancel': self.propagate_cancel,
    #         'move_dest_ids': [(4, x.id) for x in self.move_dest_ids if not byproduct_id],
    #         'cost_share': cost_share,
    #     }

    @api.depends(
        'move_raw_ids.state', 'move_raw_ids.quantity_done', 'move_finished_ids.state',
        'workorder_ids.state', 'product_qty', 'qty_producing')
    def _compute_state(self):
        """ Compute the production state. This uses a similar process to stock
        picking, but has been adapted to support having no moves. This adaption
        includes some state changes outside of this compute.

        There exist 3 extra steps for production:
        - progress: At least one item is produced or consumed.
        - to_close: The quantity produced is greater than the quantity to
        produce and all work orders has been finished.
        """

        for production in self:
            if not production.state or not production.multi_uom_line_id:
                production.state = 'draft'
            elif production.state == 'cancel' or (production.move_finished_ids and all(
                    move.state == 'cancel' for move in production.move_finished_ids)):
                production.state = 'cancel'
            elif (
                    production.state == 'done'
                    or (production.move_raw_ids and all(
                move.state in ('cancel', 'done') for move in production.move_raw_ids))
                    and all(move.state in ('cancel', 'done') for move in production.move_finished_ids)
            ):
                production.state = 'done'
            elif production.workorder_ids and all(
                    wo_state in ('done', 'cancel') for wo_state in production.workorder_ids.mapped('state')):
                production.state = 'to_close'
            elif not production.workorder_ids and float_compare(production.qty_producing, production.product_qty,
                                                                precision_rounding=production.multi_uom_line_id.uom_id.rounding) >= 0:
                production.state = 'to_close'
            elif any(wo_state in ('progress', 'done') for wo_state in production.workorder_ids.mapped('state')):
                production.state = 'progress'
            elif production.product_uom_id and not float_is_zero(production.qty_producing,
                                                                 precision_rounding=production.product_uom_id.rounding):
                production.state = 'progress'
            elif any(not float_is_zero(move.quantity_done,
                                       precision_rounding=move.product_uom.rounding or move.product_id.uom_id.rounding)
                     for move in production.move_raw_ids):
                production.state = 'progress'
