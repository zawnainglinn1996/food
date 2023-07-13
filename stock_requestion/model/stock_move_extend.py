from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.tools.misc import clean_context, OrderedSet
from odoo.exceptions import UserError
from collections import defaultdict


class StockMove(models.Model):
    _inherit = 'stock.move'
    requestion_type = fields.Selection([('issued', 'Issued'), ('received', 'Received')], string='Reqiestion Type')

    brand_id = fields.Many2one('product.brand', string='Brand',related='product_id.brand_id',store=True)
    remark = fields.Text(string='Remark')
    stock_req_id = fields.Many2one('stock.requestion.line', string='Stock Req')
    distribution_remark = fields.Char('Distribution Remark')



    def _action_done(self, cancel_backorder=False):
        res = super(StockMove, self)._action_done(cancel_backorder)
        for rec in self:
            if rec.requestion_type == 'issued':
                prev_qty = rec.stock_req_id.issued_qty
                if rec.location_id.usage == 'internal' and rec.location_dest_id.usage == 'transit':
                    sign = 1
                else:
                    sign = -1
                done_quantity = rec.quantity_done * sign
                rec.stock_req_id.issued_qty = done_quantity + prev_qty
            elif rec.requestion_type == 'received':
                prev_qty = rec.stock_req_id.received_qty
                if rec.location_id.usage == 'transit' and rec.location_dest_id.usage == 'internal':
                    sign = 1
                else:
                    sign = -1
                done_quantity = rec.quantity_done * sign
                rec.stock_req_id.received_qty = done_quantity + prev_qty

        return res

    # def _action_done(self, cancel_backorder=False):
    #
    #     # res = super(StockMove, self)._action_done
    #     # return res
    #
    #     self.filtered(lambda move: move.state == 'draft')._action_confirm()  # MRP allows scrapping draft moves
    #     moves = self.exists().filtered(lambda x: x.state not in ('done', 'cancel'))
    #     moves_ids_todo = OrderedSet()
    #
    #     # Cancel moves where necessary ; we should do it before creating the extra moves because
    #     # this operation could trigger a merge of moves.
    #     for move in moves:
    #         if move.quantity_done <= 0 and not move.is_inventory:
    #             if float_compare(move.product_uom_qty, 0.0,
    #                              precision_rounding=move.product_uom.rounding) == 0 or cancel_backorder:
    #                 move._action_cancel()
    #
    #     # Create extra moves where necessary
    #     for move in moves:
    #         if move.state == 'cancel' or (move.quantity_done <= 0 and not move.is_inventory):
    #             continue
    #
    #         moves_ids_todo |= move._create_extra_move().ids
    #
    #     moves_todo = self.browse(moves_ids_todo)
    #     moves_todo._check_company()
    #     # Split moves where necessary and move quants
    #     backorder_moves_vals = []
    #     for move in moves_todo:
    #         # To know whether we need to create a backorder or not, round to the general product's
    #         # decimal precision and not the product's UOM.
    #         rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
    #         if float_compare(move.quantity_done, move.product_uom_qty, precision_digits=rounding) < 0:
    #             # Need to do some kind of conversion here
    #             qty_split = move.product_uom._compute_quantity(move.product_uom_qty - move.quantity_done,
    #                                                            move.product_id.uom_id, rounding_method='HALF-UP')
    #             new_move_vals = move._split(qty_split)
    #             backorder_moves_vals += new_move_vals
    #     backorder_moves = self.env['stock.move'].create(backorder_moves_vals)
    #     # The backorder moves are not yet in their own picking. We do not want to check entire packs for those
    #     # ones as it could messed up the result_package_id of the moves being currently validated
    #     backorder_moves.with_context(bypass_entire_pack=True)._action_confirm(merge=False)
    #     if cancel_backorder:
    #         backorder_moves.with_context(moves_todo=moves_todo)._action_cancel()
    #     moves_todo.mapped('move_line_ids').sorted()._action_done()
    #     # Check the consistency of the result packages; there should be an unique location across
    #     # the contained quants.
    #     for result_package in moves_todo \
    #             .mapped('move_line_ids.result_package_id') \
    #             .filtered(lambda p: p.quant_ids and len(p.quant_ids) > 1):
    #         if len(result_package.quant_ids.filtered(
    #                 lambda q: not float_is_zero(abs(q.quantity) + abs(q.reserved_quantity),
    #                                             precision_rounding=q.product_uom_id.rounding)).mapped(
    #             'location_id')) > 1:
    #             raise UserError(
    #                 _('You cannot move the same package content more than once in the same transfer or split the same package into two location.'))
    #     picking = moves_todo.mapped('picking_id')
    #     moves_todo.write({'state': 'done', 'date': fields.Datetime.now()})
    #
    #     new_push_moves = moves_todo.filtered(lambda m: m.picking_id.immediate_transfer)._push_apply()
    #     if new_push_moves:
    #         new_push_moves._action_confirm()
    #     move_dests_per_company = defaultdict(lambda: self.env['stock.move'])
    #     for move_dest in moves_todo.move_dest_ids:
    #         move_dests_per_company[move_dest.company_id.id] |= move_dest
    #     for company_id, move_dests in move_dests_per_company.items():
    #         move_dests.sudo().with_company(company_id)._action_assign()
    #
    #     # We don't want to create back order for scrap moves
    #     # Replace by a kwarg in master
    #     if self.env.context.get('is_scrap'):
    #         return moves_todo
    #
    #     """FOR STOCK REQUESTION RECEIVED QUANTITY AND ISSUED QUANTITY"""
    #     if self.picking_id.is_good_received:
    #         for line in self.picking_id.move_ids_without_package:
    #             for l in self.stock_req_id:
    #                 if line.product_id == l.product_id:
    #                     l.received_qty += line.quantity_done
    #
    #     elif self.picking_id.is_good_issued:
    #         for line in self.picking_id.move_ids_without_package:
    #             for l in self.stock_req_id:
    #                 if line.product_id == l.product_id:
    #                     l.issued_qty += line.quantity_done
    #     else:
    #         pass
    #     if picking and not cancel_backorder:
    #         backorder = picking._create_backorder()
    #         if any([m.state == 'assigned' for m in backorder.move_lines]):
    #             backorder._check_entire_pack()
    #     return moves_todo
