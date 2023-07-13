from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from datetime import datetime


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_assigned = fields.Boolean(string='Assigned', default=False)
    is_good_issued = fields.Boolean(string='Issued?', default=False)
    car_way_id = fields.Many2one('car.way.name', string='Car Way Name')
    assign_status = fields.Selection([('assign_way', 'Assigned Way'), ('un_assign', 'Unassigned')], string='Way Status',
                                     default='un_assign')

    def action_assign_way(self):
        date = (self.scheduled_date + relativedelta(hours=6, minutes=30)).strftime('%d/%m/%Y %H:%M:%S')
        scheduled_date = datetime.strptime(date, '%d/%m/%Y %H:%M:%S')
        action = {
            'name': 'Assign Way',
            'type': 'ir.actions.act_window',
            'res_model': 'car.way.wizard',
            'context': {
                'default_analytic_account_id': self.analytic_account_id.id,
                'default_picking_id': self.id,
                'default_date': scheduled_date

            },
            'target': 'new',
            'view_mode': 'form',
        }
        return action
