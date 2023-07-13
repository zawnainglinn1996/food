from odoo import api, models, fields
from datetime import datetime
from dateutil.relativedelta import relativedelta


class StockInOutWizard(models.TransientModel):

    _name = 'stock.in.out.wizard'
    _description = 'Stock In/Out Wizard'

    start_date = fields.Date('Beginning Date',
                             required=True,
                             default=lambda self: fields.Date.context_today(self).replace(day=1))
    end_date = fields.Date('End Date',
                           required=True,
                           default=lambda self: fields.Date.context_today(self) + relativedelta(day=31))
    warehouse_ids = fields.Many2many('stock.warehouse', string='Warehouses', required=True)
    location_ids = fields.Many2many('stock.location', string='Locations', required=False)
    available_location_ids = fields.Many2many('stock.location',
                                              string='Available Locations',
                                              compute='_compute_available_locations')
    product_ids = fields.Many2many('product.product', string='Products', domain=[('detailed_type', '=', 'product')])
    category_ids = fields.Many2many('product.category', string='Categories')
    based_on = fields.Selection([('product', 'Product'),
                                 ('category', 'Category')], 'Based On', default='product', required=True)

    @api.depends('warehouse_ids')
    def _compute_available_locations(self):
        for rec in self:
            locations = self.env['stock.location']
            root_location_ids = rec.warehouse_ids.lot_stock_id.ids
            for root_location_id in root_location_ids:
                locations |= self.env['stock.location'].search([('id', 'child_of', root_location_id)])
            rec.available_location_ids = locations.ids

    def btn_print(self):
        data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'warehouse_ids': self.warehouse_ids.ids,
            'location_ids': self.location_ids and self.location_ids.ids or self.available_location_ids.ids,
            'product_ids': self.product_ids.ids,
            'category_ids': self.category_ids.ids,
            'based_on': self.based_on,
        }
        return self.env.ref('stock_in_out_report.report_stock_in_out_report').report_action(docids=[], data=data)
