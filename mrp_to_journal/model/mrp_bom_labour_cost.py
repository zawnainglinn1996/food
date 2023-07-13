from odoo import models, fields, api, _


class MrpBomLabourCost(models.Model):
    _name = "mrp.bom.labour.cost"
    _description = 'Mrp Bom Labour Cost'

    @api.onchange('product_id')
    def onchange_product_id(self):
        res = {}
        if not self.product_id:
            return res
        self.uom_id = self.product_id.uom_id.id
        # self.cost = self.product_id.standard_price

    @api.onchange('planned_multi_uom_qty', 'cost', 'actual_qty')
    def onchange_labour_planned_qty(self):
        for line in self:
            price = line.planned_qty * line.cost
            actual_price = line.actual_qty * line.cost
            line.total_cost = price
            line.total_actual_cost = actual_price

    def get_currency_id(self):
        user_id = self.env.uid
        res_user_id = self.env['res.users'].browse(user_id)
        for line in self:
            line.currency_id = res_user_id.company_id.currency_id

    operation_id = fields.Many2one('mrp.routing.workcenter', string="Operation")
    product_id = fields.Many2one('product.template', string="Product")
    planned_qty = fields.Float(string="Planned Qty", digits='Product Unit of Measure', default=0.0)
    actual_qty = fields.Float(string="Actual Qty", digits='Product Unit of Measure', default=0.0, compute=False)
    uom_id = fields.Many2one('uom.uom', string="UOM")
    workcenter_id = fields.Many2one('mrp.workcenter', string="Workcenter")
    cost = fields.Float(string="Planned Cost", digits='Product Unit of Measure')
    total_cost = fields.Float(compute='onchange_labour_planned_qty', digits='Product Unit of Measure', string="Total Planned Cost")
    total_actual_cost = fields.Float(compute='onchange_labour_planned_qty',  digits='Product Unit of Measure',string="Total Actual Cost")
    # total_labour_cost = fields.Float(string="Total Labour Cost")
    mrp_bom_labour_id = fields.Many2one("mrp.bom", "Mrp Bom Labour")
    mrp_pro_labour_id = fields.Many2one("mrp.production", "Mrp Production Labour")
    mrp_wo_labour_id = fields.Many2one("mrp.workorder", "Mrp Workorder Labour")
    currency_id = fields.Many2one("res.currency", compute='get_currency_id', string="Currency")

    work_center_id = fields.Many2one('mrp.workcenter', 'Work Center')
    service_product_id = fields.Many2one('product.product', string='Service Product')
    uom_id = fields.Many2one('uom.uom', 'UoM', related='service_product_id.uom_id')
    state = fields.Selection([('draft', 'Draft'),
                              ('post', 'Posted')], 'State', default='draft')

    @api.onchange('service_product_id')
    def onchange_service_product(self):
        for line in self:
            if line.service_product_id:
                line.cost = line.service_product_id.standard_price
