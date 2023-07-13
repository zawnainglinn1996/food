from odoo import api, models, fields, _


class StockRule(models.Model):

    _inherit = 'stock.rule'

    def _get_custom_move_fields(self):
        res = super(StockRule, self)._get_custom_move_fields()
        res.append('multi_uom_line_id')
        return res

    def _update_purchase_order_line(self, product_id, product_qty, product_uom, company_id, values, line):
        res = super(StockRule, self)._update_purchase_order_line(product_id,
                                                                 product_qty,
                                                                 product_uom,
                                                                 company_id,
                                                                 values,
                                                                 line)
        res['multi_uom_line_id'] = values.get('multi_uom_line_id')
        return res

    def _push_prepare_move_copy_values(self, move_to_copy, new_date):
        values = super(StockRule, self)._push_prepare_move_copy_values(move_to_copy, new_date)
        values['multi_uom_line_id'] = move_to_copy.multi_uom_line_id.id
        return values
