from odoo import api, models, fields


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    can_pack = fields.Boolean('Unit Conversion')
    parent_product_id = fields.Many2one('product.product', 'Parent Product')
    child_product_qty = fields.Float('Child Product Qty')
