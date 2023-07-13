from odoo import models,fields,api,_


class SaleReport(models.Model):
    _inherit = "sale.report"

    product_family_id = fields.Many2one('product.family', string='Product Family')
    product_group_id = fields.Many2one('product.group', string='Product Group')

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['product_family_id'] = ", t.product_family_id as product_family_id"
        fields['product_group_id'] =",t.product_group_id as product_group_id"
        groupby += ', t.product_family_id, t.product_group_id'
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)

