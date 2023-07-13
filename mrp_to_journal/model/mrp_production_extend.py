from odoo import models, fields, api, exceptions, _
from odoo.tools import float_round
from odoo.exceptions import UserError, ValidationError


class MrpUnbuild(models.Model):
    _inherit = "mrp.unbuild"

    def _compute_total_product_cost(self):
        if self.mo_id:
            self.product_unit_cost = self.mo_id.product_unit_cost

    def _compute_total_material_cost(self):
        if self.mo_id:
            self.unbuild_material_cost = self.mo_id.total_actual_material_cost

    @api.depends('mo_id')
    def _get_move_product_unbuild(self):
        if self.mo_id:
            self.move_raw_ids = self.mo_id.move_raw_ids
            self.move_byproduct_ids = self.mo_id.move_byproduct_ids

    product_unit_cost = fields.Float(compute='_compute_total_product_cost', string="Product Unit Cost",
                                     digits='Product Unit of Measure')
    move_raw_ids = fields.One2many('stock.move', 'raw_material_production_line_id', 'Components',
                                   compute='_get_move_product_unbuild', store=True)
    move_byproduct_ids = fields.One2many('stock.move', 'byproduct_line_id', 'By Product',
                                         compute='_get_move_product_unbuild', store=True)
    unbuild_material_cost = fields.Float(compute='_compute_total_material_cost', string="Material Cost",
                                         digits='Product Unit of Measure')

    def _generate_move_from_existing_move(self, move, factor, location_id, location_dest_id):
        return self.env['stock.move'].create({
            'name': self.name,
            'date': self.create_date,
            'product_id': move.product_id.id,
            'product_uom_qty': move.product_uom_qty * factor,
            'product_uom': move.product_uom.id,
            'procure_method': 'make_to_stock',
            'location_dest_id': location_dest_id.id,
            'location_id': location_id.id,
            'warehouse_id': location_dest_id.warehouse_id.id,
            'raw_material_production_line_id': move.raw_material_production_line_id.id,
            'byproduct_line_id': move.byproduct_line_id.id,
            'unbuild_id': self.id,
            'company_id': move.company_id.id,
        })


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    @api.model
    def create(self, vals):

        list_of_material = []
        list_of_labour = []
        list_of_overhead = []

        mrp_bom_obj = self.env['mrp.bom'].browse(vals['bom_id'])
        '''for material in mrp_bom_obj.bom_material_cost_ids:
            list_of_material.append(material.id)
        vals['pro_material_cost_ids'] = [(6,0,list_of_material)]'''

        res = super(MrpProduction, self).create(vals)

        if not res.planned_qty_avg:
            for labour in res.bom_id.bom_labour_cost_ids:
                vals = {'operation_id': labour.operation_id.id,
                        'product_id': labour.product_id.id,
                        'service_product_id': labour.service_product_id.id,
                        'planned_qty': labour.planned_multi_uom_qty,
                        'planned_multi_uom_qty': labour.planned_multi_uom_qty,
                        'uom_id': labour.uom_id.id,
                        'multi_uom_line_id': labour.multi_uom_line_id.id,
                        'cost': labour.cost or False,
                        'mrp_pro_labour_id': res.id,
                        'work_center_id': labour.work_center_id.id,
                        }
                labour_res = self.env["mrp.bom.labour.cost"].create(vals)
            for overhead in res.bom_id.bom_overhead_cost_ids:
                vals = {'operation_id': overhead.operation_id.id,
                        'product_id': overhead.product_id.id,
                        'service_product_id': overhead.service_product_id.id,
                        'planned_qty': overhead.planned_multi_uom_qty,
                        'planned_multi_uom_qty': overhead.planned_multi_uom_qty,
                        'uom_id': overhead.uom_id.id,
                        'multi_uom_line_id': overhead.multi_uom_line_id.id,
                        'cost': overhead.cost or False,
                        'mrp_pro_overhead_id': res.id,
                        'work_center_id': overhead.work_center_id.id,
                        }
                overhead_res = self.env["mrp.bom.overhead.cost"].create(vals)
            for material in res.bom_id.bom_material_cost_ids:
                vals = {
                    'product_id': material.product_id.id,
                    'planned_qty': material.planned_qty,
                    'planned_multi_uom_qty': material.planned_multi_uom_qty,
                    'uom_id': material.uom_id.id,
                    'multi_uom_line_id': material.multi_uom_line_id.id,
                    'actual_qty': material.planned_qty,
                    'actual_cost': material.actual_cost or False,
                    'operation_id': material.operation_id.id,
                    'mrp_pro_material_id': res.id,
                }
                material_res = self.env["mrp.bom.material.cost"].create(vals)
        else:

            for labour in res.bom_id.bom_labour_cost_ids:
                vals = {'operation_id': labour.operation_id.id,
                        'product_id': labour.product_id.id,
                        'service_product_id': labour.service_product_id.id,
                        'planned_qty': labour.planned_qty * res.planned_qty_avg,
                        'uom_id': labour.uom_id.id,
                        'multi_uom_line_id': labour.multi_uom_line_id.id,
                        'cost': labour.cost or False,
                        'mrp_pro_labour_id': res.id,
                        'work_center_id': labour.work_center_id.id,
                        }
                labour_res = self.env["mrp.bom.labour.cost"].create(vals)
            for overhead in res.bom_id.bom_overhead_cost_ids:
                vals = {'operation_id': overhead.operation_id.id,
                        'product_id': overhead.product_id.id,
                        'service_product_id': overhead.service_product_id.id,
                        'planned_qty': overhead.planned_qty * res.planned_qty_avg,
                        'uom_id': overhead.uom_id.id,
                        'multi_uom_line_id': overhead.multi_uom_line_id.id,
                        'cost': overhead.cost or False,
                        'mrp_pro_overhead_id': res.id,
                        'work_center_id': overhead.work_center_id.id,
                        }
                overhead_res = self.env["mrp.bom.overhead.cost"].create(vals)
            for material in res.bom_id.bom_material_cost_ids:
                if not material.multi_uom_line_id:
                    raise UserError(
                        _(" UOM Missing  in BOM Component's lines of Product Name - %s ! Pls insert UOM For This Product") % material.product_id.name)

                vals = {
                    'product_id': material.product_id.id,
                    'planned_qty': material.planned_qty * res.planned_qty_avg,
                    'planned_multi_uom_qty': material.planned_multi_uom_qty * res.planned_qty_avg,
                    'actual_qty': material.planned_qty * res.planned_qty_avg,
                    'uom_id': material.uom_id.id,
                    'multi_uom_line_id': material.multi_uom_line_id.id,
                    'actual_cost': material.actual_cost or False,
                    'operation_id': material.operation_id.id,
                    'mrp_pro_material_id': res.id,
                }
                material_res = self.env["mrp.bom.material.cost"].create(vals)

        return res

    def parepare_cost_value(self):

        for rec in self.move_raw_ids:
            qty = rec.multi_quantity_done
            material_id = self.pro_material_cost_ids.filtered(
                lambda l: l.product_id.id == rec.product_id.product_tmpl_id.id)
            material_id.planned_multi_uom_qty = rec.multi_uom_qty
            material_id.actual_qty = qty

    def write(self, values):
        res = super(MrpProduction, self).write(values)
        for production in self:
            bom_id = self.env['mrp.bom'].browse(values.get('bom_id'))
            qty_producing = values.get('qty_producing')
            if qty_producing:
                self.parepare_cost_value()
            if bom_id:
                bom_labour_cost_ids_vals = []
                for line in bom_id.bom_labour_cost_ids:
                    production.pro_labour_cost_ids.unlink()
                    bom_labour_cost_ids_vals.append({
                        'operation_id': line.operation_id.id,
                        'service_product_id': line.service_product_id.id,
                        'planned_qty': line.planned_qty,
                        'multi_uom_line_id': line.multi_uom_line_id.id,
                        'uom_id': line.uom_id.id,
                        'cost': line.cost,
                        'total_actual_cost': line.total_cost,
                        'mrp_pro_labour_id': production.id,
                    })
                self.env['mrp.bom.labour.cost'].create(bom_labour_cost_ids_vals)
                bom_overhead_cost_ids_vals = []
                for line in bom_id.bom_overhead_cost_ids:
                    production.pro_overhead_cost_ids.unlink()
                    bom_overhead_cost_ids_vals.append({
                        'operation_id': line.operation_id.id,
                        'service_product_id': line.service_product_id.id,
                        'planned_qty': line.planned_qty,
                        'multi_uom_line_id': line.multi_uom_line_id.id,
                        'uom_id': line.uom_id.id,
                        'cost': line.cost,
                        'total_actual_cost': line.total_cost,
                        'mrp_pro_overhead_id': production.id,
                    })
                self.env['mrp.bom.overhead.cost'].create(bom_overhead_cost_ids_vals)
                bom_material_cost_ids_vals = []

                for line in bom_id.bom_material_cost_ids:
                    production.pro_material_cost_ids.unlink()
                    bom_material_cost_ids_vals.append({
                        'operation_id': line.operation_id.id,
                        'product_id': line.product_id.id,
                        'planned_qty': production.qty_producing,
                        'planned_multi_uom_qty': line.planned_multi_uom_qty,
                        'multi_uom_line_id': line.multi_uom_line_id.id,
                        'uom_id': line.uom_id.id,
                        'actual_cost': line.actual_cost,
                        'total_actual_cost': line.total_cost,
                        'mrp_pro_material_id': production.id,
                    })
                self.env['mrp.bom.material.cost'].create(bom_material_cost_ids_vals)


            if not ('product_qty' in values and production.state == 'draft'):
                continue

            for raw in production.move_raw_ids:
                consume_qty = raw.multi_uom_line_id.ratio * production.product_multi_uom_qty
                raw.product_uom_qty = consume_qty

            for material in production.bom_id.bom_material_cost_ids:
                planned_qty = material.multi_uom_line_id.ratio * production.product_multi_uom_qty
                line = production.pro_material_cost_ids.filtered(lambda l: l.product_id.id == material.product_id.id)
                line.planned_qty = planned_qty
                line.planned_multi_uom_qty = planned_qty / material.multi_uom_line_id.ratio

            for labour_cost in production.bom_id.bom_labour_cost_ids:
                planned_qty = labour_cost.planned_qty * production.planned_qty_avg
                line = production.pro_labour_cost_ids.filtered(
                    lambda l: l.service_product_id.id == labour_cost.service_product_id.id
                )
                line.planned_qty = planned_qty

            for overhead_cost in production.bom_id.bom_overhead_cost_ids:
                planned_qty = overhead_cost.planned_qty * production.planned_qty_avg
                line = production.pro_overhead_cost_ids.filtered(
                    lambda l: l.service_product_id.id == overhead_cost.service_product_id.id
                )
                line.planned_qty = planned_qty

        return res

    def _compute_total_cost(self):
        component_total = 0.0
        component_actual_total = 0.0

        material_total = 0.0
        material_actual_total = 0.0

        labour_total = 0.0
        labour_actual_total = 0.0

        overhead_total = 0.0
        overhead_actual_total = 0.0
        total_m_cost = 0
        total_l_cost = 0
        total_o_cost = 0
        test = 0
        for line in self.pro_material_cost_ids:
            if not line.multi_uom_line_id:
                raise UserError(
                    _(" UOM Missing  in BOM Component's lines of Product Name - %s !  ") % line.product_id.name)
            # material_total += float_round(line.actual_qty * line.actual_cost,
            #                               precision_rounding=line.multi_uom_line_id.uom_id.rounding)
            # total_m_cost += float_round(line.actual_qty * line.actual_cost,
            #                             precision_rounding=line.multi_uom_line_id.uom_id.rounding)
            # material_actual_total += float_round(line.actual_qty * line.actual_cost,
            #                                      precision_rounding=line.multi_uom_line_id.uom_id.rounding)

            total_m_cost += round(line.actual_qty * line.cost, 2)
            material_total += round(line.actual_qty * line.cost, 2)
            total_m_cost += round(line.actual_qty * line.cost, 2)
            material_actual_total += round(line.actual_qty * line.cost, 2)

        total_component_cost = 0

        for line in self.move_raw_ids:
            product_price = line.product_id.standard_price
            component_total += line.product_uom_qty * product_price
            component_actual_total += line.quantity_done * product_price
            total_component_cost += component_actual_total
        for line in self.pro_labour_cost_ids:
            if not line.multi_uom_line_id:
                raise UserError(
                    _(" UOM Missing  in Labour Cost lines of Product Name - %s !  ") % line.service_product_id.name)
            labour_total += line.total_cost

            total_l_cost += float_round(line.actual_qty * line.cost,
                                        precision_rounding=line.multi_uom_line_id.uom_id.rounding)
            labour_actual_total += float_round(line.actual_qty * line.cost,
                                               precision_rounding=line.multi_uom_line_id.uom_id.rounding)

        for line in self.pro_overhead_cost_ids:
            overhead_total += line.total_cost
            total_o_cost += float_round(line.actual_qty * line.cost,
                                        precision_rounding=line.multi_uom_line_id.uom_id.rounding)
            overhead_actual_total += float_round(line.actual_qty * line.cost,
                                                 precision_rounding=line.multi_uom_line_id.uom_id.rounding)

        self.total_component_cost = component_total
        self.total_actual_component_cost = component_actual_total
        self.total_labour_cost = labour_total
        self.total_actual_labour_cost = labour_actual_total

        self.total_overhead_cost = overhead_total
        self.total_actual_overhead_cost = overhead_actual_total

        self.total_actual_material_cost = material_actual_total

        self.total_material_cost = material_total

    def _compute_total_all_cost(self):
        total = 0.0
        actual_total = 0.0
        total = self.total_labour_cost + self.total_overhead_cost + self.total_material_cost
        actual_total = self.total_actual_labour_cost + self.total_actual_overhead_cost + self.total_actual_material_cost
        self.total_all_cost = total
        self.total_actual_all_cost = actual_total

    def _compute_total_actual_qty(self):
        self.total_actual_qty = self.qty_producing

    def get_currency_id(self):
        user_id = self.env.uid
        res_user_id = self.env['res.users'].browse(user_id)
        for line in self:
            line.currency_id = res_user_id.company_id.currency_id

    def _compute_total_product_cost(self):
        sm_qty = sum(
            line.multi_qty_done for line in self.finished_move_line_ids if line.product_id.id == self.product_id.id)
        if sm_qty:
            self.product_unit_cost = self.total_actual_all_cost / sm_qty
        else:
            self.product_unit_cost = 0.0

    currency_id = fields.Many2one("res.currency", compute='get_currency_id', string="Currency")
    pro_material_cost_ids = fields.One2many("mrp.bom.material.cost", "mrp_pro_material_id", "Material Cost")
    pro_labour_cost_ids = fields.One2many("mrp.bom.labour.cost", "mrp_pro_labour_id", "Labour Cost")
    pro_overhead_cost_ids = fields.One2many("mrp.bom.overhead.cost", "mrp_pro_overhead_id", "Overhead Cost")
    pro_total_material_cost = fields.Float(string="Pro Total Material Cost", digits='Product Unit of Measure')
    planned_qty_avg = fields.Float('Planned Avg', digits='Product Unit of Measure', compute='_compute_planned_qty_avg',
                                   store=True)
    planned_qty_producing = fields.Float('Planned Qty Avg', digits='Product Unit of Measure',
                                         compute='_compute_planned_qty_producing', store=True)

    # Costing Tab
    total_material_cost = fields.Float(compute='_compute_total_cost', string="Total Material Cost",
                                       digits='Product Unit of Measure')
    total_component_cost = fields.Float(compute='_compute_total_cost', string='Total Component Cost',
                                        digits='Product Unit of Measure')
    total_labour_cost = fields.Float(compute='_compute_total_cost', string="Total Labour Cost",
                                     digits='Product Unit of Measure')
    total_overhead_cost = fields.Float(compute='_compute_total_cost', string="Total Overhead Cost",
                                       digits='Product Unit of Measure')
    total_all_cost = fields.Float(compute='_compute_total_all_cost', string="Total Cost",
                                  digits='Product Unit of Measure')

    # Costing Tab
    total_actual_material_cost = fields.Float(compute='_compute_total_cost', string="Total Actual Material Cost",
                                              digits='Product Unit of Measure')
    total_actual_component_cost = fields.Float(compute='_compute_total_cost', string='Total Actual Component Cost')
    total_actual_labour_cost = fields.Float(compute='_compute_total_cost', string="Total Actual Labour Cost",
                                            digits='Product Unit of Measure')
    total_actual_overhead_cost = fields.Float(compute='_compute_total_cost', string="Total Actual Overhead Cost",
                                              digits='Product Unit of Measure')
    total_actual_all_cost = fields.Float(compute='_compute_total_all_cost', string="Total Actual Cost",
                                         digits='Product Unit of Measure')

    total_actual_qty = fields.Float(compute='_compute_total_actual_qty', string='Finished Actual Qty',
                                    digits='Product Unit of Measure')

    product_unit_cost = fields.Float(compute='_compute_total_product_cost',
                                     string="Product Unit Cost", digits='Product Unit of Measure')


    @api.depends('bom_id', 'product_qty')
    def _compute_planned_qty_avg(self):
        for production in self:
            if production.bom_id:
                production.planned_qty_avg = production.product_qty / production.bom_id.product_qty
            else:
                production.planned_qty_avg = 0.00

    @api.depends('bom_id', 'qty_producing')
    def _compute_planned_qty_producing(self):
        for production in self:
            if production.bom_id:
                production.planned_qty_producing = production.qty_producing / production.bom_id.product_qty
            else:
                production.planned_qty_producing = 0.00

    @api.onchange('qty_producing')
    def onchange_qty_producing(self):
        for production in self:
            production._set_qty_producing()

            if production.qty_producing:

                for material in production.bom_id.bom_material_cost_ids:
                    planned_qty = material.planned_qty * production.product_multi_uom_qty
                    line = production.pro_material_cost_ids.filtered(
                        lambda l: l.product_id.id == material.product_id.id)
                    line.planned_qty = planned_qty
                    line.planned_multi_uom_qty = planned_qty / material.multi_uom_line_id.ratio

                for labour_cost in production.bom_id.bom_labour_cost_ids:
                    planned_qty = labour_cost.planned_qty * production.product_qty
                    line = production.pro_labour_cost_ids.filtered(
                        lambda l: l.service_product_id.id == labour_cost.service_product_id.id)
                    line.planned_qty = planned_qty

                    line.actual_qty = planned_qty

                for overhead_cost in production.bom_id.bom_overhead_cost_ids:
                    planned_qty = overhead_cost.planned_qty * production.product_qty
                    line = production.pro_overhead_cost_ids.filtered(
                        lambda l: l.service_product_id.id == overhead_cost.service_product_id.id)
                    line.planned_qty = planned_qty
                    line.actual_qty = production.qty_producing

                for rec in production.move_raw_ids:
                    bom_component_id = production.bom_id.bom_line_ids.filtered(lambda l: l.product_id == rec.product_id)
                    if len(bom_component_id) > 1:
                        raise UserError(
                            _(" Please check on BOM Component's lines of  Product Name  - %s ! This should be one line ") % rec.product_id.name)
                    standard_qty = production.product_qty * bom_component_id.product_qty
                    difference_qty = (production.qty_producing * bom_component_id.product_qty) - standard_qty
                    standard_qty = float_round((production.qty_producing - production.qty_produced) * rec.unit_factor,
                                               precision_rounding=rec.product_uom.rounding)

                    rec.update({
                        'standard_qty': standard_qty / rec.multi_uom_line_id.ratio,
                        'difference_qty': -1 * (standard_qty)
                    })
