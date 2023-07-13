from odoo import fields, models, api, _


class ShopToTake(models.Model):
    _name = 'shop.to.take'
    _description = 'Shop To Take'

    name = fields.Char('ယူမည့်ဆိုင်')
    phone = fields.Char('ယူမည့်ဆိုင်ဖုန်း')

