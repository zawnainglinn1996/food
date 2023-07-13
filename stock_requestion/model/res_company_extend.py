from odoo import models,fields,api,_


class Company(models.Model):
    _inherit = "res.company"

    short_code = fields.Char(string='Short Code')