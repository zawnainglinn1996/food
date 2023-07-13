from random import randint

from odoo import models, fields, api, _


class CarWay(models.Model):
    _name = 'car.way'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Car Way Form'
    _rec_name = 'reference'

    date = fields.Date(string='Date', default=fields.Date.context_today)
    way_line_ids = fields.One2many('car.way.line', 'way_id', string='Brand List')
    reference = fields.Char(string='Ref')

    @api.model
    def create(self, vals):
        vals['reference'] = self.env['ir.sequence'].next_by_code('car.way') or _('New')
        res = super(CarWay, self).create(vals)
        return res

    def action_car_way_report(self):
        ways = []
        for way in self:
            way_lines = []
            count = 1
            company_id = self.env.company
            user = self.env.user
            for line in way.way_line_ids:
                way_lines.append({
                    'way_no': line.car_name,
                    'way_name': line.way_name.name,
                    'shop_name': ', '.join(line.analytic_account_id.mapped('name')),
                    'remark': line.remark,
                    'no': count,
                    'tray': line.tray,
                })
                count += 1
            ways.append({
                'reference': way.reference,
                'date': way.date.strftime("%d/%m/%Y"),
                'c_name': company_id.name,
                'c_image': company_id.logo,
                'lines': way_lines,
            })

        return self.env.ref('car_way.action_report_car_way').report_action([], {
            'ways': ways
        })


class CarWayLine(models.Model):
    _name = 'car.way.line'
    _description = 'Car Way Line'

    car_name = fields.Char('Car Name')
    way_name = fields.Many2one('car.way.name', string='Car Name')
    analytic_account_id = fields.Many2many('account.analytic.account', 'account_analytic_account_car_way_line_rel',
                                           'car_way_line_id', 'account_analytic_account_id', string='Branch Name')
    remark = fields.Text(string='Remark')
    way_id = fields.Many2one('car.way', string='Way')
    tray = fields.Char(string='Tray')


class AnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'
    color = fields.Integer('color index')





