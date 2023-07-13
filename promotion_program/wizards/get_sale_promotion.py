from odoo import api, models, fields, _
from odoo.exceptions import UserError
from markupsafe import Markup
from odoo.addons.promotion_program.models.promotion_program import OrderLine, Reward


class GetSalePromotion(models.Model):
    _name = 'get.sale.promotion'
    _description = 'Get Sale Promotion'

    order_id = fields.Many2one('sale.order', string='Order ID')
    order_line = fields.One2many('sale.order.line', 'order_id', string='Order Lines')
    currency_id = fields.Many2one('res.currency', strig='Currency')
    company_id = fields.Many2one('res.company', string='Company ID')
    product_id = fields.Many2one('product.product', string='Product')
    # buy_one_get_one_line_ids = fields.One2many('buy.one.get.one.line', 'promotion_id', 'Buy 1 Get 1 Lines')
    date_order = fields.Datetime(string='Order Date', default=fields.Datetime.now)
    promotion_ids = fields.Many2many('promotion.program',
                                     'get_sale_promotion_rel',
                                     'order_id',
                                     'promotion_id',
                                     'Promotions', compute=False)

    @api.onchange('order_id')
    def onchange_order_id(self):
        programs = []
        for order in self:
            order_lines = order.order_id.order_line
            available_promotion_ids = []
            for order_line in order_lines:
                if order.order_id.team_id and order.date_order:
                    date = fields.Datetime.context_timestamp(order, order.date_order).date()
                    promotion_ids = self.env['promotion.program']._get_available_promotions(date=date,
                                                                                            teams=order.order_id.team_id)
                else:
                    promotion_ids = []
                for promotion_id in promotion_ids:
                    if promotion_id.type == 'buy_one_get_one':
                        for line_id in promotion_id.buy_one_get_one_line_ids:
                            if order_line.product_id == line_id.product_x_id:
                                if order_line.product_uom_qty >= line_id.product_x_qty:
                                    available_promotion_ids.append(
                                        promotion_id
                                    )
                    elif promotion_id.type == 'discount_total_amount':

                        subtotal = order.order_id.amount_total
                        if subtotal >= promotion_id.total_invoice_amount:
                            available_promotion_ids.append(
                                promotion_id
                            )
            for rec in available_promotion_ids:
                programs.append(rec.id)
            return {'domain': {'promotion_ids': [('id', 'in', programs)]}}

    def action_select_promotion(self):

        rewards = {}
        applied_promotions = False
        self.order_id.remove_promotions()

        date = fields.Datetime.context_timestamp(self, self.date_order).date()

        lines = [OrderLine(line.id,
                           line.product_id.id,
                           line.product_uom._compute_quantity(line.product_uom_qty, line.product_id.uom_id),
                           line.product_uom.id,
                           self.currency_id._convert(line.price_unit,
                                                     self.company_id.currency_id,
                                                     self.company_id,
                                                     date),
                           self.currency_id._convert(line.price_subtotal,
                                                     self.company_id.currency_id,
                                                     self.company_id,
                                                     date),
                           ) for line in self.order_id.order_line]
        order_amount = self.order_id.currency_id._convert(self.order_id.amount_total,
                                                          self.order_id.company_id.currency_id,
                                                          self.order_id.company_id,
                                                          date)

        for promotion in self.promotion_ids:
            method = getattr(promotion, f'_apply_{promotion.type}')

            promotion_rewards = method(lines, order_amount)
            if promotion_rewards:
                rewards[promotion.id] = promotion_rewards
        lines_to_create = []
        promotion_product_list = []
        for key, promotion_rewards in rewards.items():
            for reward in promotion_rewards:
                applied_promotions = True
                if type(reward) == Reward:
                    promotion = self.env['promotion.program'].browse(reward.promotion_id)
                    price = self.company_id.currency_id._convert(reward.price,
                                                                 self.currency_id,
                                                                 self.company_id,
                                                                 date)


                    values = {
                        'name': reward.description,
                        'product_id': reward.product_id,
                        'price_unit': price,
                        'product_uom_qty': reward.qty,
                        'multi_uom_line_id':reward.multi_uom_line_id,
                        'order_id': self.order_id.id,
                        'promotion_id': promotion.id,
                        'tax_id': False,
                        'promotion_account_id': reward.account_id,
                        'sequence': 1000,
                    }
                    lines_to_create.append(values)

        self.env['sale.order.line'].create(lines_to_create)

        if applied_promotions:
            return {
                'effect': {
                    'type': 'rainbow_man',
                    'message': 'Promotions applied.',
                }
            }
