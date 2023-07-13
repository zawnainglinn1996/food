from odoo import api, models, fields


class StockQuant(models.Model):

    _inherit = 'stock.quant'

    multi_uom_onhand_qty = fields.Char('Multi UOM On Hand Qty', compute='convert_to_multi_uom')
    multi_uom_diff_qty = fields.Char('Multi UOM Diff Qty', compute='convert_diff_to_multi_uom')

    @api.depends('quantity')
    def convert_to_multi_uom(self):
        for rec in self:
            total_consumed_qty = 0
            multi_uom_qty = ''
            rec.multi_uom_onhand_qty = False
            product = rec.product_id
            qty = rec.quantity
            if product.multi_uom_ok and product.multi_uom_line_ids:
                lines = product.multi_uom_line_ids
                lines = sorted(lines, key=lambda l: l.ratio, reverse=True)
                remaining_qty = qty
                for line in lines:
                    if total_consumed_qty == qty:
                        break
                    converted_qty = remaining_qty / line.ratio
                    if abs(converted_qty) >= 1:
                        multi_uom_qty += f' {int(converted_qty)} {line.uom_id.name} '
                        consumed_qty = int(converted_qty) * line.ratio
                        remaining_qty -= consumed_qty
                        total_consumed_qty += consumed_qty
            else:
                multi_uom_qty = f'{qty} {product.uom_id.name}'
            rec.multi_uom_onhand_qty = multi_uom_qty

    @api.depends('inventory_diff_quantity')
    def convert_diff_to_multi_uom(self):
        for rec in self:
            total_consumed_qty = 0
            multi_uom_qty = ''
            product = rec.product_id
            qty = rec.inventory_diff_quantity
            if product.multi_uom_ok and product.multi_uom_line_ids:
                lines = product.multi_uom_line_ids
                lines = sorted(lines, key=lambda l: l.ratio, reverse=True)
                remaining_qty = qty
                for line in lines:
                    if total_consumed_qty == qty:
                        break
                    converted_qty = remaining_qty / line.ratio
                    if abs(converted_qty) >= 1:
                        multi_uom_qty += f' {int(converted_qty)} {line.uom_id.name} '
                        consumed_qty = int(converted_qty) * line.ratio
                        remaining_qty -= consumed_qty
                        total_consumed_qty += consumed_qty
            else:
                multi_uom_qty = f'{qty} {product.uom_id.name}'
            rec.multi_uom_diff_qty = multi_uom_qty
