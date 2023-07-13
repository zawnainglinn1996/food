from odoo import api, models, fields


class CrmTeam(models.Model):

    _inherit = 'crm.team'

    promotion_ids = fields.Many2many('promotion.program', 
                                     'promotion_sales_team_rel', 
                                     'team_id', 
                                     'promotion_id', 'Promotion Programs')
