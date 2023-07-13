from odoo import api, models, fields, _


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    multi_uom_line_ids = fields.Many2many('multi.uom.line', compute='compute_multi_uom_line_ids')
    multi_uom_line_id = fields.Many2one('multi.uom.line', 'Multi UOM')
    product_multi_uom_qty = fields.Float('Multi Request Qty', default=1.0,
                                         digits='Product Unit of Measure', required=True, tracking=2)


    @api.depends('product_tmpl_id')
    def compute_multi_uom_line_ids(self):
        for rec in self:
            rec.multi_uom_line_ids = []
            if rec.product_tmpl_id.multi_uom_line_ids:
                rec.multi_uom_line_ids = rec.product_tmpl_id.multi_uom_line_ids.ids

    @api.onchange('product_tmpl_id')
    def product_id_change(self):
        for rec in self:
            if rec.product_tmpl_id:
                line = rec.product_tmpl_id.multi_uom_line_ids.filtered(lambda l: l.is_default_uom == True)
                rec.multi_uom_line_id = line

    @api.onchange('product_tmpl_id', 'multi_uom_line_id')
    def _change_multi_uom_qty(self):
        for rec in self:
            if rec.product_id and rec.product_multi_uom_qty and rec.multi_uom_line_id:
                rec.product_qty = rec.multi_uom_line_id.ratio * rec.product_multi_uom_qty


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    multi_uom_line_ids = fields.Many2many('multi.uom.line', compute='compute_multi_uom_line_ids')
    multi_uom_line_id = fields.Many2one('multi.uom.line', 'Multi UOM')
    product_multi_uom_qty = fields.Float('Multi Request Qty', default=1.0,
                                         digits='Product Unit of Measure', tracking=2)
    real_product_qty = fields.Float(string='Real Product Qty', compute='compute_real_product_qty')

    @api.depends('product_multi_uom_qty')
    def compute_real_product_qty(self):
        self.real_product_qty = 0.0
        for rec in self:
            if rec.product_multi_uom_qty:
                rec.real_product_qty = rec.product_multi_uom_qty

    @api.depends('product_id')
    def compute_multi_uom_line_ids(self):
        for rec in self:
            rec.multi_uom_line_ids = []
            if rec.product_id.multi_uom_line_ids:
                rec.multi_uom_line_ids = rec.product_id.multi_uom_line_ids.ids

    @api.onchange('product_id')
    def product_id_change(self):
        for rec in self:
            if rec.product_id:
                line = rec.product_id.multi_uom_line_ids.filtered(lambda l: l.is_default_uom == True)
                rec.multi_uom_line_id = line

    @api.onchange('product_multi_uom_qty', 'product_id', 'multi_uom_line_id')
    def _change_multi_uom_qty(self):
        for rec in self:

            if rec.product_id and rec.product_multi_uom_qty and rec.multi_uom_line_id:
                rec.product_qty = rec.multi_uom_line_id.ratio * rec.product_multi_uom_qty
                rec.product_uom_id = rec.product_id.uom_id.id


class MrpBomByProduct(models.Model):
    _inherit = "mrp.bom.byproduct"

    multi_uom_line_ids = fields.Many2many('multi.uom.line', compute='compute_multi_uom_line_ids')
    multi_uom_line_id = fields.Many2one('multi.uom.line', 'Multi UOM')
    product_multi_uom_qty = fields.Float('Multi Request Qty', default=1.0,
                                         digits='Product Unit of Measure', tracking=2)

    @api.depends('product_id')
    def compute_multi_uom_line_ids(self):
        for rec in self:
            rec.multi_uom_line_ids = []
            if rec.product_id.multi_uom_line_ids:
                rec.multi_uom_line_ids = rec.product_id.multi_uom_line_ids.ids

    @api.onchange('product_id')
    def product_id_change(self):
        for rec in self:
            if rec.product_id:
                line = rec.product_id.multi_uom_line_ids.filtered(lambda l: l.is_default_uom == True)
                rec.multi_uom_line_id = line

    @api.onchange('product_multi_uom_qty', 'product_id', 'multi_uom_line_id')
    def _change_multi_uom_qty(self):
        for rec in self:
            if rec.product_id and rec.product_multi_uom_qty and rec.multi_uom_line_id:
                rec.product_qty = rec.multi_uom_line_id.ratio * rec.product_multi_uom_qty
