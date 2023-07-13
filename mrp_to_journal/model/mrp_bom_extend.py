from odoo import models, fields, api, _


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    def _compute_total_cost(self):
        material_total = 0.0
        labour_total = 0.0
        overhead_total = 0.0

        for line in self.bom_material_cost_ids:
            material_total += line.total_cost

        for line in self.bom_labour_cost_ids:
            labour_total += line.total_cost

        for line in self.bom_overhead_cost_ids:
            overhead_total += line.total_cost

        self.bom_total_material_cost = material_total
        self.bom_total_labour_cost = labour_total
        self.bom_total_overhead_cost = overhead_total

    def get_currency_id(self):
        user_id = self.env.uid
        res_user_id = self.env['res.users'].browse(user_id)
        for line in self:
            line.currency_id = res_user_id.company_id.currency_id

    @api.model_create_multi
    def create(self, vals_list):
        res = super(MrpBom, self).create(vals_list)
        for material in res.bom_line_ids:
            vals = {
                'product_id': material.product_id.product_tmpl_id.id,
                'planned_multi_uom_qty': material.product_multi_uom_qty,
                'planned_qty': material.product_qty,

                'multi_uom_line_id': material.multi_uom_line_id.id,
                'cost': material.product_id.standard_price * material.multi_uom_line_id.ratio,
                'mrp_bom_material_id': res.id,
            }
            res.write({'bom_material_cost_ids': [(0, 0, vals)]})
        config = self.env['res.config.settings'].search([], order="id desc", limit=1)

        if config.process_costing == 'workcenter':
            for line in res.bom_labour_cost_ids:
                line.unlink()
            for line in res.bom_overhead_cost_ids:
                line.unlink()
            for operation in res.operation_ids:
                value = {
                    'operation_id': operation.id,
                    'workcenter_id': operation.workcenter_id.id,
                    'cost': operation.workcenter_id.labour_costs_hour or False,
                    'mrp_bom_labour_id': res.id,

                }

                if operation.time_cycle > 0:
                    value.update({'planned_qty': operation.time_cycle / 60})
                res.write({'bom_labour_cost_ids': [(0, 0, value)]})

            for operation in res.operation_ids:
                value = {
                    'operation_id': operation.id,
                    'workcenter_id': operation.workcenter_id.id,
                    'cost': operation.workcenter_id.overhead_cost_hour or False,
                    'mrp_bom_overhead_id': res.id,

                }
                if operation.time_cycle > 0:
                    value.update({'planned_qty': operation.time_cycle / 60})
                res.write({'bom_overhead_cost_ids': [(0, 0, value)]})

        return res

    def write(self, vals):
        res = super(MrpBom, self).write(vals)
        config = self.env['res.config.settings'].search([], order="id desc", limit=1)
        if vals.get('bom_line_ids'):

            for line in self.bom_material_cost_ids:
                line.unlink()

            for material in self.bom_line_ids:
                vals = {
                    'product_id': material.product_id.product_tmpl_id.id,
                    'planned_multi_uom_qty': material.product_multi_uom_qty,
                    'planned_qty':material.product_qty,
                    'multi_uom_line_id': material.multi_uom_line_id.id,
                    'cost': material.product_id.standard_price * material.multi_uom_line_id.ratio,
                    'mrp_bom_material_id': self.id,
                }
                material_obj = self.env['mrp.bom.material.cost'].create(vals)
        if vals.get('routing_id') and config.process_costing == 'workcenter':
            mrp_routing_obj = self.env['mrp.routing'].browse(vals.get('routing_id'))
            for line in self.bom_labour_cost_ids:
                line.unlink()
            for line in self.bom_overhead_cost_ids:
                line.unlink()
            for operation in mrp_routing_obj.operation_ids:
                value = {
                    'operation_id': operation.id,
                    'workcenter_id': operation.workcenter_id.id,
                    'cost': operation.workcenter_id.labour_costs_hour or False,
                    'mrp_bom_labour_id': self.id,
                }
                if operation.time_cycle > 0:
                    value.update({'planned_qty': operation.time_cycle / 60})
                self.write({'bom_labour_cost_ids': [(0, 0, value)]})

            for operation in mrp_routing_obj.operation_ids:
                value = {
                    'operation_id': operation.id,
                    'workcenter_id': operation.workcenter_id.id,
                    'cost': operation.workcenter_id.overhead_cost_hour or False,
                    'mrp_bom_overhead_id': self.id,

                }
                if operation.time_cycle > 0:
                    value.update({'planned_qty': operation.time_cycle / 60})
                self.write({'bom_overhead_cost_ids': [(0, 0, value)]})

        return res

    bom_material_cost_ids = fields.One2many("mrp.bom.material.cost", "mrp_bom_material_id", "Material Cost")
    bom_labour_cost_ids = fields.One2many("mrp.bom.labour.cost", "mrp_bom_labour_id", "Labour Cost")
    bom_overhead_cost_ids = fields.One2many("mrp.bom.overhead.cost", "mrp_bom_overhead_id", "Overhead Cost")

    # single page total cost
    bom_total_material_cost = fields.Float(compute='_compute_total_cost', string="Total Material Cost", default=0.0,digits='Product Unit of Measure')
    bom_total_labour_cost = fields.Float(compute='_compute_total_cost', string="Total Labour Cost", default=0.0,digits='Product Unit of Measure')
    bom_total_overhead_cost = fields.Float(compute='_compute_total_cost', string="Total Overhead Cost", default=0.0,digits='Product Unit of Measure')
    currency_id = fields.Many2one("res.currency", compute='get_currency_id', string="Currency")
