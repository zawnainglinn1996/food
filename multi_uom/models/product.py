from odoo import api, models, fields, _
from odoo.exceptions import ValidationError, UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    multi_uom_ok = fields.Boolean('Multi UOM', copy=False, default=True)
    multi_uom_line_ids = fields.One2many('multi.uom.line', 'product_tmpl_id', 'Multi UOM Lines')
    uom_category_id = fields.Many2one('uom.category', 'UOM Category', related='uom_id.category_id', store=True)

    def _compute_item_count(self):
        mode = self.env['ir.config_parameter'].sudo().get_param('product.product_pricelist_setting')
        if mode != 'uom':
            return super()._compute_item_count()
        for template in self:
            template.pricelist_item_count = self.env['pricelist.item.uom'].search_count(
                [('product_id', '=', template.product_variant_id.id)])

    def open_pricelist_rules(self):
        mode = self.env['ir.config_parameter'].sudo().get_param('product.product_pricelist_setting')
        if mode != 'uom':
            return super().open_pricelist_rules()
        return {
            'name': 'Price Rules',
            'type': 'ir.actions.act_window',
            'res_model': 'pricelist.item.uom',
            'views': [(self.env.ref('multi_uom.view_pricelist_item_uom_tree').id, 'tree'), (False, 'form')],
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': [('product_id', '=', self.product_variant_id.id)],
            'context': {
                'default_product_id': self.product_variant_id.id,
            },
        }

    @api.model
    def create(self, vals):
        template = super().create(vals)
        product_uom_id = template.uom_id.id
        multi_uom_lines = template.multi_uom_line_ids
        product_uom_line = multi_uom_lines.filtered(lambda l: l.uom_id.id == product_uom_id)
        count_list = []
        if not product_uom_line:
            self.env['multi.uom.line'].create({
                'uom_id': product_uom_id,
                'ratio': 1,
                'price': 1,
                'product_tmpl_id': template.id,
            })
        for rec in multi_uom_lines:
            if rec.is_default_uom:
                count_list.append(rec.is_default_uom)
        if len(count_list) > 1:
            raise ValidationError('Default UOM Should be One Line')
        return template

    def write(self, values):
        res = super(ProductTemplate, self).write(values)
        count_list = []
        for rec in self.multi_uom_line_ids:
            if rec.is_default_uom:
                count_list.append(rec.is_default_uom)
        if len(count_list)>1:
            raise ValidationError('Default UOM Should be One Line')
        return res


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def open_pricelist_rules(self):
        mode = self.env['ir.config_parameter'].sudo().get_param('product.product_pricelist_setting')
        if mode != 'uom':
            return super().open_pricelist_rules()
        return {
            'name': 'Price Rules',
            'type': 'ir.actions.act_window',
            'res_model': 'pricelist.item.uom',
            'view_mode': 'tree,form',
            'views': [('multi_uom.view_pricelist_item_uom_tree', 'tree'), (False, 'form')],
            'target': 'current',
            'domain': [('product_id', '=', self.id)],
            'context': {
                'default_product_id': self.id,
            },
        }


class MultiUOMLine(models.Model):
    _name = 'multi.uom.line'
    _description = 'Multi UOM Line'
    _order = 'ratio'
    _rec_name = 'uom_id'

    uom_id = fields.Many2one('uom.uom', 'UOM')
    price = fields.Float('Price')
    ratio = fields.Float('Ratio', compute=False)
    product_tmpl_id = fields.Many2one('product.template', 'Product Template')
    remark = fields.Char(string='Ratio Remark')
    is_default_uom = fields.Boolean(string='Default UOM?')

    @api.constrains('ratio')
    def _check_ratio(self):
        for rec in self:
            if rec.ratio == 0:
                raise ValidationError('Ratio can\'t be zero.')

    def _compute_quantity(self, qty):
        self.ensure_one()
        return qty * self.ratio

    def write(self, values):
        product_ids = self.product_tmpl_id.product_variant_ids.ids
        moves = self.env['stock.move'].search([('product_id', 'in', product_ids)])
        if moves and ('uom_id' in values or 'ratio' in values):
            raise UserError('You can\'t edit UoM and ratio since there are transactions.')
        return super(MultiUOMLine, self).write(values)

    def unlink(self):
        for record in self:
            product_ids = record.product_tmpl_id.product_variant_ids.ids
            moves = self.env['stock.move'].search([('product_id', 'in', product_ids)])
            if moves:
                raise UserError(_('You can not delete this UOM Line'))
        return super(MultiUOMLine, self).unlink()
