from odoo import api, models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    group_uom_price = fields.Boolean("UoM Pricelists",
                                     implied_group='multi_uom.group_uom_price')
    product_pricelist_setting = fields.Selection(selection_add=[('uom', 'UoM Price')])

    @api.onchange('group_product_pricelist')
    def _onchange_group_sale_pricelist(self):
        if not self.group_product_pricelist and self.group_sale_pricelist:
            self.group_sale_pricelist = False
        if not self.group_product_pricelist and self.group_uom_price:
            self.group_uom_price = False

    @api.onchange('product_pricelist_setting')
    def _onchange_product_pricelist_setting(self):
        if self.product_pricelist_setting == 'advanced':
            self.group_sale_pricelist = True
            self.group_uom_price = False
        elif self.product_pricelist_setting == 'uom':
            self.group_sale_pricelist = False
            self.group_uom_price = True
        else:
            self.group_sale_pricelist = self.group_uom_price = False
