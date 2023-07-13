from odoo import api, models, fields
from odoo.addons.promotion_program.models.promotion_program import OrderLine, Reward


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    promotion_ids = fields.Many2many('promotion.program', 
                                     'order_promotion_rel', 
                                     'order_id', 
                                     'promotion_id', 
                                     'Promotions', 
                                     compute='_compute_promotion_ids')

    @api.depends('date_order', 'team_id')
    def _compute_promotion_ids(self):
        for order in self:
            if order.team_id and order.date_order:
                date = fields.Datetime.context_timestamp(order, order.date_order).date()
                order.promotion_ids = self.env['promotion.program']._get_available_promotions(date=date, 
                                                                                              teams=order.team_id)
            else:
                order.promotion_ids = []

    def apply_promotion(self):
        action = {
            'name': 'Select Promotion',
            'type': 'ir.actions.act_window',
            'res_model': 'get.sale.promotion',
            'context': {
                'default_date_order': self.date_order,
                'default_partner_id': self.partner_id.id,
                'default_order_id': self.id,
                'default_currency_id': self.currency_id.id,
                'default_company_id': self.company_id.id,
            },
            'target': 'new',
            'view_mode': 'form',
        }
        return action

    def remove_promotions(self):
        promotion_lines = self.order_line.filtered(lambda l: l.promotion_id)
        promotion_lines.unlink()


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    promotion_id = fields.Many2one('promotion.program', 'Promotion')
    promotion_account_id = fields.Many2one('account.account', 'Promotion COA')

    def _prepare_invoice_line(self, **optional_values):
        values = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        if self.promotion_account_id and self.product_id:
            values['name'] = self.product_id.name_get()[0][1]
        values['promotion_id'] = self.promotion_id.id
        values['promotion_account_id'] = self.promotion_account_id.id
        return values
