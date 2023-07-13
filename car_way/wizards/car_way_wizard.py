from odoo import api, models, fields, _
from odoo.exceptions import ValidationError, UserError
from odoo import SUPERUSER_ID
from dateutil.relativedelta import relativedelta
from datetime import datetime

class CarWayWizard(models.TransientModel):
    _name = 'car.way.wizard'
    _description = 'Car Way Wizard'

    name_id = fields.Many2one('car.way.name', 'Way')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    picking_id = fields.Many2one('stock.picking', string='Picking')
    date = fields.Date('Date')



    def assign_way(self):
        way_data = self.env['car.way'].search([('date', '=', self.date)])
        piaking_name = self.picking_id.name
        self.picking_id.is_assigned = True
        self.picking_id.assign_status = 'assign_way'
        self.picking_id.car_way_id = self.name_id.id
        if self.name_id:
            picking_date = self.picking_id.scheduled_date+ relativedelta(hours=6, minutes=30,seconds=0)
            if self.date != picking_date.date():
                raise UserError(
                    _("Assign Date Should be Issue Date -%s") % picking_date.date())

        if not way_data:
            if not self.analytic_account_id:
                raise ValidationError(
                    _("Current Picking Does Not Have Analytic Account")
                )
            assign_wan = self.env['car.way'].with_user(SUPERUSER_ID).create({
                'date': self.date,
                'way_line_ids': [
                    (0, 0,
                     {
                         'way_name': self.name_id.id,
                         'analytic_account_id': self.analytic_account_id,
                     }
                     )
                ], }
            )
        else:
            if not self.analytic_account_id:
                raise ValidationError(
                    _("Current Picking Does Not Have Analytic Account")
                )
            if way_data.way_line_ids:

                line = way_data.way_line_ids.filtered(lambda l: l.way_name.id == self.name_id.id)
                if line:
                    line.with_user(SUPERUSER_ID).write({'analytic_account_id': [(4, self.analytic_account_id.id)]})
                else:
                    way_data.with_user(SUPERUSER_ID).write({
                        'way_line_ids': [
                            (0, 0,
                             {'way_id': way_data.id,
                              'way_name': self.name_id.id,
                              'analytic_account_id': self.analytic_account_id,
                              }
                             )
                        ],
                    })

            else:
                if not self.analytic_account_id:
                    raise ValidationError(
                        _("Current Picking Does Not Have Analytic Account")
                    )
                way_data.with_user(SUPERUSER_ID).write({
                    'way_line_ids': [
                        (0, 0,
                         {'way_id': way_data.id,
                          'way_name': self.name_id.id,
                          'analytic_account_id': self.analytic_account_id,
                          }
                         )
                    ],

                })
        action = {
            'name': 'Message',
            'type': 'ir.actions.act_window',
            'res_model': 'alert.delivery',
            'context': {
                'default_alert_name': 'Picking with reference ID ' + piaking_name + ' has been assigned.',
            },
            'target': 'new',
            'view_mode': 'form',
        }

        return action


class AlertDelivery(models.TransientModel):
    _name = 'alert.delivery'
    _description = 'Alert When Deliver man has been assigned'

    alert_name = fields.Char(string='Alert')
