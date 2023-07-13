from odoo import models, fields, api, _
from odoo.http import request


class PosPayment(models.Model):
    _inherit = 'pos.payment'

    def check_access_payment(self):

        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])
            id = self.env.context.get('active_id')
            context = dict(self.env.context)
            if id:
                context['search_default_config_id'] = [id]
            if employee_id and employee_id.user_id.is_concurrent_user:
                allow_pos_locations = employee_id.pos_location_ids.ids

                if allow_pos_locations:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': ('Payments'),
                        'res_model': 'pos.payment',
                        'view_mode': 'tree,kanban,form',
                        'domain': [('session_id.config_id.location_id', 'in', allow_pos_locations)],
                        'context': {},
                    }
                else:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': ('Payments'),
                        'res_model': 'pos.payment',
                        'view_mode': 'tree,kanban,form',
                        'domain': [('session_id.config_id.location_id', 'in', allow_pos_locations)],
                        'context': {},
                    }
            else:
                pos_counters = self.env['pos.location'].search([])
                return {
                    'type': 'ir.actions.act_window',
                    'name': ('Payments'),
                    'res_model': 'pos.payment',
                    'view_mode': 'tree,kanban,form',
                    'domain': [('session_id.config_id.location_id', 'in', pos_counters)],
                    'context': {},
                }
