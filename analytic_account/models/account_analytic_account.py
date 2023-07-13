from odoo import models, fields, api, _


class AccountAnalytic(models.Model):
    _inherit = 'account.analytic.account'

    from_shop_ph = fields.Char('မှာသည့်ဆိုင်ဖုန်း')
    shop_to_take_id = fields.Many2one('shop.to.take', 'ယူမည့်ဆိုင်')
    shop_to_take_ph = fields.Char('ယူမည့်ဆိုင်ဖုန်း')

    @api.onchange('shop_to_take_id')
    def onchange_shop_to_take_ph(self):
        shop = []
        for rec in self:
            if rec.shop_to_take_id:
                self.shop_to_take_ph = rec.shop_to_take_id.phone

