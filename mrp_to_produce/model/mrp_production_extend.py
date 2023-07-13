from odoo import models, fields, api, _


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    standard_quantity = fields.Float(string='Standard Qty', compute='compute_standard_qty', digits='Product Unit of Measure', default=0.0, store=True)
    difference_quantity = fields.Float(string='Difference Qty', compute='compute_difference_qty', digits='Product Unit of Measure', default=0.0,
                                       store=True)
    is_mo_create = fields.Boolean('Created MO', compute='_compute_is_create', default=False, copy=False)
    mrp_produce_count = fields.Integer('MO Count', default=0.0,  digits='Product Unit of Measure',compute='_compute_mo_produce_id')
    product_multi_uom_qty = fields.Float('Multi Request Qty', default=1.0,
                                         digits='Product Unit of Measure', readonly=True, required=True, tracking=True,
                                         states={'draft': [('readonly', False)]})

    def action_confirm(self):
        res = super(MrpProduction,self).action_confirm()
        for rec in self.move_raw_ids:
            rec.standard_qty = rec.multi_uom_qty
            rec.difference_qty = -1 * rec.multi_uom_qty
        return res

    @api.depends('product_multi_uom_qty', 'state')
    def compute_standard_qty(self):
        for rec in self:
            if rec.product_qty and rec.state == 'confirmed':
                rec.standard_quantity = rec.product_multi_uom_qty

    @api.depends('product_multi_uom_qty', 'standard_quantity')
    def compute_difference_qty(self):
        for rec in self:
            if rec.product_qty:
                rec.difference_quantity = rec.multi_qty_producing - rec.standard_quantity

    def _compute_is_create(self):
        self.is_mo_create = False
        mo_produces = self.env['mrp.produce'].search([('mrp_production_id', '=', self.id)])
        if mo_produces:
            self.is_mo_create = True

    def button_mo_produce(self):
        self.is_mo_create = True
        self.env['mrp.produce'].sudo().create([{
            'mrp_production_id': self.id,
            'name': self.name,
            'date': self.date_planned_start.date() or False,
            'fg_product_id': self.product_id.id,
            'standard_qty': self.standard_quantity or 0.0,
            'uom_id': self.product_id.uom_id.id,
            'multi_uom_line_id': self.multi_uom_line_id.id,
        }])
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Successfully Created MO Produce',
                'type': 'rainbow_man',
            }
        }

    def _compute_mo_produce_id(self):
        for rec in self:
            produce_orders = self.env['mrp.produce'].search([('mrp_production_id', '=', self.id)])
            rec.mrp_produce_count = len(produce_orders)

    def action_mo_produce(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Manufacturing Order Produce'),
            'res_model': 'mrp.produce',
            'view_mode': 'tree,form',
            'domain': [('mrp_production_id', '=', self.id)],
        }
