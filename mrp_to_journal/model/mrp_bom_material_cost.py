from odoo import models, fields, api, _


class MrpBomMaterialCost(models.Model):
    _name = "mrp.bom.material.cost"
    _description = 'Mrp Bom Material Cost'

    operation_id = fields.Many2one('mrp.routing.workcenter', string="Operation")
    product_id = fields.Many2one('product.template', string="Product")
    planned_qty = fields.Float(string="Planned Qty", digits='Product Unit of Measure', default=0.0)
    actual_qty = fields.Float(string="Actual Qty", digits='Product Unit of Measure', default=0.0, compute=False)
    uom_id = fields.Many2one('uom.uom', string="UOM")
    cost = fields.Float(string="Planned Cost", digits='Product Unit of Measure', related='product_id.standard_price')
    actual_cost = fields.Float(string='Unit Cost', digits='Product Unit of Measure', compute='_compute_actual_cost')
    total_cost = fields.Float(compute='onchange_planned_qty', digits='Product Unit of Measure',
                              string="Total Planned Cost")
    total_actual_cost = fields.Float(compute='onchange_planned_qty', digits='Product Unit of Measure',
                                     string="Total Actual Cost")
    mrp_bom_material_id = fields.Many2one("mrp.bom", "Mrp Bom Material")
    mrp_pro_material_id = fields.Many2one("mrp.production", "Mrp Production Material")
    mrp_wo_material_id = fields.Many2one("mrp.workorder", "Mrp Workorder Material")
    currency_id = fields.Many2one("res.currency", compute='get_currency_id', string="Currency")

    def _compute_actual_cost(self):
        for material in self:
            price_unit = material.multi_uom_line_id.ratio * material.product_id.standard_price
            material.actual_cost = price_unit
            # material.actual_cost = material.planned_qty * price_unit
            #material.actual_cost = material.product_id.standard_price

    def get_currency_id(self):
        user_id = self.env.uid
        res_user_id = self.env['res.users'].browse(user_id)
        for line in self:
            line.currency_id = res_user_id.company_id.currency_id

    @api.onchange('product_id')
    def onchange_product_id(self):
        res = {}
        if not self.product_id:
            return res
        self.uom_id = self.product_id.uom_id.id

    @api.onchange('planned_qty', 'actual_cost', 'actual_qty')
    def onchange_planned_qty(self):
        for line in self:
            price = line.planned_multi_uom_qty * line.actual_cost
            actual_price = line.planned_multi_uom_qty * line.actual_cost
            line.total_cost = price
            line.total_actual_cost = actual_price
