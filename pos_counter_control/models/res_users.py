from odoo import api, models, fields


class Users(models.Model):

    _inherit = 'res.users'

    pos_location_ids = fields.Many2many('pos.location','pos_location_user_rel','user_id','pos_location_id','Allow Pos Counter Location')


