from odoo import models, fields, api, _


class PosLocation(models.Model):
    _name = 'pos.location'
    _description = 'POS Location'

    name = fields.Char(string='Name')
    description = fields.Text(string='Description')
    color = fields.Integer('color index')
