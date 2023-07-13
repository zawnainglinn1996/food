import pytz
from odoo import models, fields


class StockBackdateReportWizard(models.TransientModel):

    _name = 'stock.backdate.report.wizard'
    _description = 'Stock Backdate Report Wizard'

    date = fields.Datetime('Date', default=fields.Datetime.now)

    def btn_show_report(self):
        user_tz = pytz.timezone(self.env.context.get('tz') or 'utc')
        user_date = pytz.utc.localize(self.date, is_dst=None).astimezone(user_tz)
        return {
            'name': user_date.strftime("%d/%m/%Y %I:%M %p"),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.backdate.report',
            'view_mode': 'tree,form',
            'context': {'inventory_date': self.date},
            'target': 'current',
        }
