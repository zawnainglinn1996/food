from odoo import api, models, fields, _
from odoo.exceptions import ValidationError, UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def convert_to_multi_uom(self, qty):
        total_consumed_qty = 0
        multi_uom_qty = ''
        multi_uom_line_ids = self.multi_uom_line_ids
        if len(multi_uom_line_ids) > 1 and qty != 0:
            lines = multi_uom_line_ids
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
            multi_uom_qty = f'{self.uom_id.name}'
        return multi_uom_qty
