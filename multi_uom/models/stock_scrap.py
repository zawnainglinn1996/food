from odoo import api, models, fields


class StockScrap(models.Model):

    _inherit = 'stock.scrap'

    scrap_qty = fields.Float(compute='compute_multi_uom_scrap_qty',
                             inverse='set_multi_uom_scrap_qty', store=True)

    multi_uom_line_id = fields.Many2one('multi.uom.line', 'Multi UoM Line')
    multi_uom_qty = fields.Float('Multi UoM Quantity', default=1.0, required=True,
                                 states={'done': [('readonly', True)]},
                                 digits='Product Unit of Measure')
    multi_uom_line_ids = fields.Many2many('multi.uom.line', compute='compute_multi_uom_line_ids')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = super(StockScrap, self)._onchange_product_id()
        line = self.product_id.multi_uom_line_ids.filtered(lambda l: l.uom_id.id == self.product_id.uom_id.id)
        self.multi_uom_line_id = line.id
        return res

    @api.depends('multi_uom_line_id', 'multi_uom_qty')
    def compute_multi_uom_scrap_qty(self):
        for rec in self:
            rec.scrap_qty = rec.multi_uom_qty * rec.multi_uom_line_id.ratio

    def set_multi_uom_scrap_qty(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.multi_uom_qty = rec.scrap_qty / rec.multi_uom_line_id.ratio
            else:
                rec.multi_uom_qty = rec.scrap_qty

    @api.depends('product_id')
    def compute_multi_uom_line_ids(self):
        for rec in self:
            rec.multi_uom_line_ids = rec.product_id.multi_uom_line_ids.ids

    def _prepare_move_values(self):
        values = super(StockScrap, self)._prepare_move_values()
        values['multi_uom_line_id'] = self.multi_uom_line_id.id
        return values


# class MultiScrapLine(models.Model):
#
#     _inherit = 'multi.scrap.line'
#
#     scrap_qty = fields.Float(compute='compute_multi_uom_scrap_qty',
#                              inverse='set_multi_uom_scrap_qty', store=True)
#     multi_uom_line_id = fields.Many2one('multi.uom.line', 'Multi UoM Line')
#     multi_uom_qty = fields.Float('Multi UoM Quantity', default=1.0, required=True, digits='Product Unit of Measure')
#     multi_uom_line_ids = fields.Many2many('multi.uom.line', compute='compute_multi_uom_line_ids')
#
#     @api.onchange('product_id')
#     def onchange_product_id(self):
#         res = super(MultiScrapLine, self).onchange_product_id()
#         line = self.product_id.multi_uom_line_ids.filtered(lambda l: l.uom_id.id == self.product_id.uom_id.id)
#         self.multi_uom_line_id = line.id
#         return res
#
#     @api.depends('multi_uom_line_id', 'multi_uom_qty')
#     def compute_multi_uom_scrap_qty(self):
#         for rec in self:
#             rec.scrap_qty = rec.multi_uom_qty * rec.multi_uom_line_id.ratio
#
#     def set_multi_uom_scrap_qty(self):
#         for rec in self:
#             if rec.multi_uom_line_id:
#                 rec.multi_uom_qty = rec.scrap_qty / rec.multi_uom_line_id.ratio
#             else:
#                 rec.multi_uom_qty = rec.scrap_qty
#
#     @api.depends('product_id')
#     def compute_multi_uom_line_ids(self):
#         for rec in self:
#             rec.multi_uom_line_ids = rec.product_id.multi_uom_line_ids.ids
#
#     def _prepare_move_values(self):
#         values = super(MultiScrapLine, self)._prepare_move_values()
#         values['multi_uom_line_id'] = self.multi_uom_line_id.id
#         return values
