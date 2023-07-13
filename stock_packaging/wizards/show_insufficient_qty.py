from odoo import api, models, fields


class ShowInsufficientQty(models.TransientModel):

    _name = 'show.insufficient.qty'
    _description = 'Show Insufficient Qty'

    packing_id = fields.Many2one('stock.packaging', 'Packing', required=1)
    line_ids = fields.One2many('show.insufficient.qty.line', 'parent_id', 'Lines')

    def btn_confirm(self):
        self.packing_id.with_context(do_it_anyway=True).btn_validate()


class ShowInsufficientQtyLine(models.TransientModel):

    _name = 'show.insufficient.qty.line'
    _description = 'Show Insufficient Qty Line'

    product_id = fields.Many2one('product.product', 'Product')
    product_name = fields.Char('Product Name', related='product_id.name', store=True)
    required_qty = fields.Float('Required Qty')
    current_qty = fields.Float('Current Qty')
    parent_id = fields.Many2one('show.insufficient.qty', 'Parent')
