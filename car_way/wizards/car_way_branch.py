from odoo import api, models, fields
from datetime import datetime
from dateutil.relativedelta import relativedelta


class CarWayBranch(models.TransientModel):
    _name = 'car.way.branch'
    _description = 'Car Way Branch'

    date = fields.Date('Beginning Date', required=True, default=fields.Date.context_today)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    car_way_id = fields.Many2one('car.way.name', 'Car Way name')

    def print_report(self):
        data = {
            'date': self.date,
            'analytic_account_id': self.analytic_account_id.id,
            'car_way_id': self.car_way_id.id
        }
        return self.env.ref('car_way.car_way_branch_report').report_action(docids=[], data=data)
