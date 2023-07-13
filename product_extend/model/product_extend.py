import itertools
from odoo import models, fields, api, _,tools


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    brand_id = fields.Many2one('product.brand', string='Brand')
    short_code = fields.Char(string='Short Code', related='brand_id.short_code')
    product_family_id = fields.Many2one('product.family', string='Product Family')
    product_group_id = fields.Many2one('product.group', string='Product Group')
    mini_by_main = fields.Char('Minimum Level by Main')
    mini_by_s1 = fields.Char('Minimum Level by S1')
    mini_by_s2 = fields.Char('Minimum Level by S2')
    mini_by_d2 = fields.Char(string='Distribution')

    @tools.ormcache()
    def _get_default_uom_id(self):
        # Deletion forbidden (at least through unlink)
        return self.env.ref('uom.product_uom_unit')

    uom_id = fields.Many2one(
        'uom.uom', 'Unit of Measure',
        default=_get_default_uom_id, required=True,tracking=True,
        help="Default unit of measure used for all stock operations.")
    uom_po_id = fields.Many2one(
        'uom.uom', 'Purchase UoM',tracking=True,
        default=_get_default_uom_id, required=True,
        help="Default unit of measure used for purchase orders. It must be in the same category as the default unit of measure.")


class ProductProduct(models.Model):
    _inherit = 'product.product'

    brand_id = fields.Many2one('product.brand', string='Brand', related="product_tmpl_id.brand_id", store=True)
    short_code = fields.Char(string='Short Code', related='brand_id.short_code', store=True)
    product_family_id = fields.Many2one('product.family', string='Product Family',
                                        related='product_tmpl_id.product_family_id', store=True)
    product_group_id = fields.Many2one('product.group', string='Product Group',
                                       related='product_tmpl_id.product_group_id', store=True)




