from odoo import fields, models, api, _

class ProductExtend(models.Model):
    _inherit = "mrp.production"

    def action_confirm(self):
        res = super(ProductExtend, self).action_confirm()
        product_ids = self.env['product.template'].search([('id','=',self.product_id.product_tmpl_id.id)])
        product_ids.write({'mf_date': self.date_planned_start})
        return res