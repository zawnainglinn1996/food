from odoo import models, fields, api, _
from odoo.http import request


class PosConfig(models.Model):
    _inherit = 'pos.config'

    location_id = fields.Many2one('pos.location', string='POS Locatation')

    def action_pos_order(self):
        location_ids = self.env.user.employee_id.pos_location_ids
        return {
            'type': 'ir.actions.act_window',
            'name': ('Orders'),
            'res_model': 'pos.order',
            'view_mode': 'tree,form,kanban,pivot',
            'domain': [('location_id', 'in', location_ids.ids), ('config_id', '=', self.id)],
        }

    def action_pos_session(self):
        location_ids = self.env.user.employee_id.pos_location_ids
        return {
            'type': 'ir.actions.act_window',
            'name': ('Sessions'),
            'res_model': 'pos.session',
            'view_mode': 'tree,kanban,form',
            'domain': [('config_id.location_id', 'in', location_ids.ids), ('config_id', '=', self.id)],
        }

    def check_access_pos(self):
        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])

            if employee_id and employee_id.user_id.is_concurrent_user:
                allow_pos_locations = employee_id.pos_location_ids.ids

                if allow_pos_locations:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': ('Point of Sale'),
                        'res_model': 'pos.config',
                        'view_mode': 'tree,form',
                        'domain': [('location_id', 'in', allow_pos_locations)],
                        'context': {},
                    }
                else:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': ('Point of Sale'),
                        'res_model': 'pos.config',
                        'view_mode': 'tree,form',
                        'domain': [('location_id', 'in', [])],
                        'context': {},
                    }
            else:
                pos_counters = self.env['pos.location'].search([])
                return {
                    'type': 'ir.actions.act_window',
                    'name': ('Point of Sale'),
                    'res_model': 'pos.config',
                    'view_mode': 'tree,form',
                    'domain': [('location_id', 'in', pos_counters.ids)],
                    'context': {},
                }

    def check_access_config(self):
        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])

            if employee_id and employee_id.user_id.is_concurrent_user:
                allow_pos_locations = employee_id.pos_location_ids.ids

                if allow_pos_locations:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': ('Point of Sale'),
                        'res_model': 'pos.config',
                        'view_mode': 'kanban,tree,form',
                        'domain': [('location_id', 'in', allow_pos_locations)],
                        'context': {},
                    }
                else:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': ('Point of Sale'),
                        'res_model': 'pos.config',
                        'view_mode': 'kanban,tree,form',
                        'domain': [('location_id', 'in', [])],
                        'context': {},
                    }
            else:
                pos_counters = self.env['pos.location'].search([])
                return {
                    'type': 'ir.actions.act_window',
                    'name': ('Point of Sale'),
                    'res_model': 'pos.config',
                    'view_mode': 'kanban,tree,form',
                    'domain': [('location_id', 'in', pos_counters.ids)],
                    'context': {},
                }
