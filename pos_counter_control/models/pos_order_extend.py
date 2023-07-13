from odoo import api, models, fields
from odoo.http import request


class PosOrder(models.Model):
    _inherit = 'pos.order'
    config_id = fields.Many2one('pos.config', string='POS Config ID', related='session_id.config_id', store=True)
    location_id = fields.Many2one('pos.location', string='Location ID', related='config_id.location_id', store=True)

    def check_access_order(self):

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
                        'name': ('Orders'),
                        'res_model': 'pos.order',
                        'view_mode': 'tree,form,kanban,pivot',
                        'domain': [('location_id', 'in', allow_pos_locations)],
                        'context': context,
                    }
                else:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': ('Orders'),
                        'res_model': 'pos.order',
                        'view_mode': 'tree,form,kanban,pivot',
                        'domain': [('location_id', 'in', allow_pos_locations)],
                        'context': context,
                    }
            else:
                pos_counters = self.env['pos.location'].search([])
                return {
                    'type': 'ir.actions.act_window',
                    'name': ('Orders'),
                    'res_model': 'pos.order',
                    'view_mode': 'tree,form,kanban,pivot',
                    'domain': [('location_id', 'in', pos_counters)],
                    'context': context,
                }


class PosSession(models.Model):
    _inherit = 'pos.session'

    def check_access_pos_session(self):
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
                        'name': ('Sessions'),
                        'res_model': 'pos.session',
                        'view_mode': 'tree,kanban,form',
                        'domain': [('config_id.location_id', 'in', allow_pos_locations), ],
                        'context': {},
                    }
                else:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': ('Sessions'),
                        'res_model': 'pos.session',
                        'view_mode': 'tree,kanban,form',
                        'domain': [('config_id.location_id', 'in', allow_pos_locations), ],
                        'context': {},
                    }
            else:
                pos_counters = self.env['pos.location'].search([])
                return {
                    'type': 'ir.actions.act_window',
                    'name': ('Sessions'),
                    'res_model': 'pos.session',
                    'view_mode': 'tree,kanban,form',
                    'domain': [('config_id.location_id', 'in', pos_counters), ],
                    'context': {},
                }
