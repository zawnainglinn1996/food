from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_round

class MrpProduce(models.Model):
    _name = 'mrp.produce'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Manufacturing Order To Produce'

    state = fields.Selection([("draft", "Draft"), ("confirm", "Confirmed")],
                             'State',
                             default="draft",tracking=True )
    name = fields.Char(string='Name')
    date = fields.Date(string='Manufacturing Order Date')
    mo_number = fields.Char(string='MO Sequence Number')
    fg_product_id = fields.Many2one('product.product', string='Finished Goods Name')
    standard_qty = fields.Float(string='Standard Qty', digits='Product Unit of Measure')
    uom_id = fields.Many2one('uom.uom', string='UOM')
    multi_uom_line_id = fields.Many2one('multi.uom.line', 'Multi UOM')
    real_quantity = fields.Float(string='Real Quantity', digits='Product Unit of Measure',tracking=True)
    mrp_production_id = fields.Many2one('mrp.production', 'Manufacturing Production')

    def button_confirm(self):
        if self.real_quantity <= 0:
            raise UserError(_('Pls Set Real Quantity '))
        self.mrp_production_id.write({
            'multi_qty_producing':self.real_quantity
        })
        self.mrp_production_id._onchange_producing()
        production = self.mrp_production_id
        for rec in self.mrp_production_id.move_raw_ids:
            qty = float_round((production.qty_producing - production.qty_produced) * rec.unit_factor,precision_rounding=rec.product_uom.rounding)
            material_id = production.pro_material_cost_ids.filtered(lambda l: l.product_id.id == rec.product_id.product_tmpl_id.id)
            material_id.actual_qty = qty
            material_id.planned_multi_uom_qty = qty / rec.multi_uom_line_id.ratio

        self.write({'state': 'confirm'})




    @api.model
    def create(self, vals):
        vals['mo_number'] = vals['name'] + '/' + self.env['ir.sequence'].next_by_code(
            'mrp.produce.seq') or _('New')
        res = super(MrpProduce, self).create(vals)
        return res

    def unlink(self):
        if not 'draft' in self.mapped('state'):
            raise UserError(_('You cannot delete a MO Produce which is Confirmed.'))
        return super(MrpProduce, self).unlink()
