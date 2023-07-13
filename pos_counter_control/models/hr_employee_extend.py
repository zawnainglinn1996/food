from odoo import api, models, fields
from odoo.http import request


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    pos_location_ids = fields.Many2many('pos.location', 'pos_location_employee_rel', 'employee_id', 'pos_location_id',
                                        'Allow Pos Counter Location')
