from odoo import models,fields,api,_


class ProductProduct(models.Model):
    _inherit = "product.product"

    def name_get(self):
        if self.env.context.get('group_by_no_leaf_inherit') or self.env.context.get('product_name_only'):
            return [(record.id, record.name) for record in self]

        return super().name_get()
