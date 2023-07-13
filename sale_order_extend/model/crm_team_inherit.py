from odoo import api, models, fields,_


class CrmTeam(models.Model):

    _inherit = 'crm.team'

    team_logo = fields.Image('Logo')
    header = fields.Char(string='Shop Header')

