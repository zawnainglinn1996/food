from odoo import models, fields, api, _


class CarWayName(models.Model):
    _name = 'car.way.name'
    _description = 'Car Way Name Form'
    _rec_name = 'name'

    name = fields.Char('Way Name')