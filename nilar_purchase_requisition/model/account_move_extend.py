from odoo import models,fields,api,_


class AccountMoveExtend(models.Model):
    _inherit = 'account.move'

    picking_number = fields.Char(string='Picking Number')