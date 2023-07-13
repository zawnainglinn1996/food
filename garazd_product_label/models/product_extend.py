from odoo import fields, models, api, _


class ProductExtend(models.Model):
    _inherit = "product.template"

    mf_date = fields.Date(string="Manufacturing Date", readonly=True)


