from odoo import models, fields, api, _


class Company(models.Model):
    _inherit = 'res.company'

    process_costing = fields.Selection([('manually', 'Manually'), ('workcenter', 'Work-Center')],
                                       string="Process Costing Method", default="manually")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    process_costing = fields.Selection(string="Process Costing Method",
                                       related="company_id.process_costing", readonly=False)
