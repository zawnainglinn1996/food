from odoo import api, models, fields


class Company(models.Model):

    _inherit = 'res.company'

    package_location_id = fields.Many2one('stock.location', 'Package Location', domain=[('usage', '=', 'inventory')])

    def assign_package_location_id(self):
        self.package_location_id = self.env.ref('stock_packaging.packaging_location')


class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    package_location_id = fields.Many2one('stock.location', 'Package Location', domain=[('usage', '=', 'inventory')],
                                          related='company_id.package_location_id', readonly=False)
