from odoo import api, models, fields, exceptions, _
from odoo.exceptions import ValidationError


class ProductPricelist(models.Model):

    _inherit = 'product.pricelist'

    pricelist_item_uom_ids = fields.One2many('pricelist.item.uom', 'pricelist_id', 'Pricelist Item UoM Lines')
    pricelist_uom_id = fields.Many2one('pricelist.item.uom', 'Pricelist Item UOM')
    pricelist_qty = fields.Float('Quantity', related='pricelist_uom_id.pricelist_qty')

    def _get_pricelist_uom_price(self, product, multi_uom_line, multi_uom_qty):
        items = self.env['pricelist.item.uom'].search([('product_id', '=', product.id),
                                                      ('multi_uom_line_id', '=', multi_uom_line.id),
                                                      ('pricelist_id', '=', self.id)])

        if items:
            pricelist_items = []
            for item in items:
                if item.pricelist_qty <= multi_uom_qty:
                    pricelist_items.append(item.pricelist_qty)

            pricelist_qty_sorting = sorted(pricelist_items)
            i = len(pricelist_qty_sorting)
            price = False
            for item in items:
                if item.pricelist_qty == pricelist_qty_sorting[i-1]:
                    price = item.price
            return price
        else:
            raise exceptions.ValidationError(
                _('!!! Please Add Pricelist For This Product !!!')
            )


class PricelistItemUom(models.Model):

    _name = 'pricelist.item.uom'
    _description = 'UoM Pricelist Item'

    product_id = fields.Many2one('product.product', 'Product', required=True)
    product_tmpl_id = fields.Many2one('product.template',
                                       string='Multi UoM Lines',
                                       related='product_id.product_tmpl_id',
                                       required=True)
    multi_uom_line_id = fields.Many2one('multi.uom.line', 'Multi UoM Line', required=True)
    uom_id = fields.Many2one('uom.uom', related='multi_uom_line_id.uom_id')
    price = fields.Float('Price', required=True)
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist', ondelete='cascade')
    pricelist_qty = fields.Float('Quantity')

    # @api.constrains('product_id', 'multi_uom_line_id', 'pricelist_id')
    # def _check_duplicate_record(self):
    #     for rec in self:
    #         duplicate = self.search([('product_id', '=', rec.product_id.id),
    #                                  ('multi_uom_line_id', '=', rec.multi_uom_line_id.id),
    #                                  ('pricelist_id', '=', rec.pricelist_id.id),
    #                                  ('id', '!=', rec.id)])
    #         if duplicate:
    #             raise ValidationError(f'Record already exists.\n\nName - {rec.product_id.name}'
    #                                   f'\nUoM - {rec.multi_uom_line_id.uom_id.name}\nPricelist - {rec.pricelist_id.name}')
