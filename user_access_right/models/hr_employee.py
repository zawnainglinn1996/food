from odoo import models, fields, api, _

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    sale_confirm = fields.Boolean('Access Confirm Button')