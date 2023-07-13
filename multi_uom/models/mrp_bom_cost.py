from odoo import api, models, fields, _


class MrpBomMaterialCost(models.Model):
    _inherit = "mrp.bom.material.cost"

    multi_uom_line_ids = fields.Many2many('multi.uom.line', compute='compute_multi_uom_line_ids')
    multi_uom_line_id = fields.Many2one('multi.uom.line', 'Multi UOM')
    planned_multi_uom_qty = fields.Float('Multi Planned Qty', default=1.0,
                                         digits='Product Unit of Measure', tracking=2)
    actual_multi_uom_qty = fields.Float('Multi Actual Qty', default=0.0, compute='_get_multi_actual_qty',
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

    @api.onchange('planned_multi_uom_qty', 'product_id', 'multi_uom_line_id')
    def _change_multi_uom_qty(self):
        for rec in self:
            if rec.product_id and rec.planned_multi_uom_qty and rec.multi_uom_line_id:
                rec.planned_qty = rec.multi_uom_line_id.ratio * rec.planned_multi_uom_qty

    @api.onchange('actual_multi_uom_qty', 'product_id', 'multi_uom_line_id')
    def _change_multi_uom_actual_qty(self):
        for rec in self:
            if rec.product_id and rec.actual_multi_uom_qty and rec.multi_uom_line_id:
                print('check check check check check ------------------------------------------')
                rec.actual_qty = rec.multi_uom_line_id.ratio * rec.actual_multi_uom_qty

    def _get_multi_actual_qty(self):
        for material in self:
            material.actual_multi_uom_qty = material.planned_multi_uom_qty


class MrpBomLabourCost(models.Model):
    _inherit = "mrp.bom.labour.cost"

    multi_uom_line_ids = fields.Many2many('multi.uom.line', compute='compute_multi_uom_line_ids')
    multi_uom_line_id = fields.Many2one('multi.uom.line', 'Multi UOM')
    planned_multi_uom_qty = fields.Float('Multi Planned Qty', default=1.0,
                                         digits='Product Unit of Measure', tracking=2)
    actual_multi_uom_qty = fields.Float('Multi Actual Qty', default=0.0,
                                        digits='Product Unit of Measure', tracking=2)

    @api.depends('service_product_id')
    def compute_multi_uom_line_ids(self):
        for rec in self:
            rec.multi_uom_line_ids = []
            if rec.service_product_id.multi_uom_line_ids:
                rec.multi_uom_line_ids = rec.service_product_id.multi_uom_line_ids.ids

    @api.onchange('service_product_id')
    def service_product_id_change(self):
        for rec in self:
            if rec.service_product_id:
                line = rec.service_product_id.multi_uom_line_ids.filtered(lambda l: l.is_default_uom == True)
                rec.multi_uom_line_id = line


class MrpBomOverHeadCost(models.Model):
    _inherit = "mrp.bom.overhead.cost"

    multi_uom_line_ids = fields.Many2many('multi.uom.line', compute='compute_multi_uom_line_ids')
    multi_uom_line_id = fields.Many2one('multi.uom.line', 'Multi UOM')
    planned_multi_uom_qty = fields.Float('Multi Planned Qty', default=1.0,
                                         digits='Product Unit of Measure', tracking=2)
    actual_multi_uom_qty = fields.Float('Multi Actual Qty', default=0.0,
                                        digits='Product Unit of Measure', tracking=2)

    @api.depends('service_product_id')
    def compute_multi_uom_line_ids(self):
        for rec in self:
            rec.multi_uom_line_ids = []
            if rec.service_product_id.multi_uom_line_ids:
                rec.multi_uom_line_ids = rec.service_product_id.multi_uom_line_ids.ids

    @api.onchange('service_product_id')
    def service_product_id_change(self):
        for rec in self:
            if rec.service_product_id:
                line = rec.service_product_id.multi_uom_line_ids.filtered(lambda l: l.is_default_uom == True)
                rec.multi_uom_line_id = line
