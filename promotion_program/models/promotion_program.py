import math
from math import floor
from odoo.exceptions import ValidationError
from odoo import api, models, fields

OPERATOR = [('=', 'Equal'), ('>=', 'Greater than or Equal')]
PROMOTION_TYPES = [('buy_one_get_one', 'Buy 1, Get 1'),
                   ('discount_total_amount', 'Discount On Total Amount')]
REWARD_TYPES = [('discount_amount', 'Discount Amount'), ('percentage', 'Percentage'), ('foc_product', 'FOC Product')]


class OrderLine:

    def __init__(self, id, product_id, qty, uom, price, subtotal):
        self.id = id
        self.product_id = product_id
        self.qty = qty
        self.uom = uom
        self.price = price
        self.subtotal = subtotal

    @staticmethod
    def mapped(self, attribute):
        data = []
        for obj in self:
            data.append(getattr(obj, attribute))
        return data


class Reward:

    def __init__(self, product_id, qty, promotion_id, multi_uom_line_id=False, price=0, account_id=False,
                 description=''):
        self.product_id = product_id
        self.qty = qty
        self.price = price
        self.multi_uom_line_id = multi_uom_line_id
        self.promotion_id = promotion_id
        self.account_id = account_id
        self.description = description


class PromotionProgram(models.Model):
    _name = 'promotion.program'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Promotion Program'

    name = fields.Char('Name', required=True)
    code = fields.Char('Code')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id, required=True)
    active = fields.Boolean('Active', default=True)
    type = fields.Selection(PROMOTION_TYPES, 'Promotion Type', default='buy_one_get_one', required=True)
    buy_one_get_one_line_ids = fields.One2many('buy.one.get.one.line', 'promotion_id', 'Buy 1 Get 1 Lines')
    team_ids = fields.Many2many('crm.team', 'promotion_sales_team_rel', 'promotion_id', 'team_id', 'Sales Teams')
    config_ids = fields.Many2many('pos.config', 'promotion_pos_config_rel', 'promotion_id', 'config_id', 'POS Counters')

    """DISCOUNT ON TOTAL AMOUNT"""

    total_invoice_amount = fields.Float(string='Total Invoice Amount')
    operator = fields.Selection(OPERATOR, 'Operator', default='=')
    discount_product_id = fields.Many2one('product.product', string='Discount Product')
    reward_type = fields.Selection(REWARD_TYPES, string='Reward Types', default='discount_amount')
    fixed_discount = fields.Float(string='Discount (Fixed)')
    account_id = fields.Many2one('account.account', 'COA')
    product_qty = fields.Float(string='Qty')
    color = fields.Integer('color index')

    @api.onchange('reward_type')
    def onchange_reward_type(self):

        for rec in self:
            if rec.reward_type:
                if rec.reward_type != 'foc_product':
                    product_ids = self.env['product.product'].search(
                        [('available_in_pos', '=', True), ('detailed_type', '=', 'service')])
                    if product_ids:
                        return {'domain': {'discount_product_id': [('id', 'in', product_ids)]}}
                    else:
                        return {'domain': {'discount_product_id': []}}
                else:
                    foc_product_ids = self.env['product.product'].search(
                        [('available_in_pos', '=', True), ('detailed_type', '!=', 'service')])
                    if foc_product_ids:
                        return {'domain': {'discount_product_id': [('id', 'in', foc_product_ids)]}}
                    else:
                        return {'domain': {'discount_product_id': []}}
            else:
                return {'domain': {'discount_product_id': []}}

    def toggle_active(self):
        active = self.filtered(lambda p: p.active)
        inactive = self - active
        active.write({'active': False})
        inactive.write({'active': True})

    @api.constrains('type', 'buy_one_get_one_line_ids')
    def _check_buy_one_get_one(self):
        for program in self:
            if program.type == 'buy_one_get_one' and not program.buy_one_get_one_line_ids:
                raise ValidationError('Please add at least a line.')

    def _get_available_promotions(self, date, teams=None, configs=None):
        domain = []
        promotions = self.browse()
        if teams:
            domain += [('team_ids', 'in', teams.ids)]
        if configs:
            domain += [('config_ids', 'in', configs.ids)]
        candidates = self.search(domain)
        for candidate in candidates:
            start_date = candidate.start_date
            end_date = candidate.end_date
            if (not start_date and not end_date) or \
                    (start_date and end_date and start_date <= date <= end_date) or \
                    (start_date and not end_date and date >= start_date) or \
                    (not start_date and end_date and date <= end_date):
                promotions |= candidate
        return promotions

    def _apply_buy_one_get_one(self, order_lines, order_amount):
        rewards = []
        order_product_ids = OrderLine.mapped(order_lines, 'product_id')
        lines = self.buy_one_get_one_line_ids.filtered(lambda l: l.product_x_id.id in order_product_ids)
        for line in lines:
            total_qty = sum(
                OrderLine.mapped([ol for ol in order_lines if ol.product_id == line.product_x_id.id], 'qty'))
            if line.operator == '=':
                qty = floor(total_qty / line.product_x_qty) * line.product_y_qty
            else:
                qty = line.product_y_qty
            if qty > 0:
                product = line.product_y_id.id
                uom = product.multi_uom_line_ids.filtered(lambda l: l.is_default_uom == True).id
                rewards.append(Reward(product_id=line.product_y_id.id,
                                      multi_uom_line_id=uom,
                                      qty=qty,
                                      price=0,
                                      promotion_id=self.id,
                                      account_id=line.account_id.id,
                                      description=f'FOC for Purchasing {line.product_x_id.name}'))
        return rewards

    def _apply_discount_total_amount(self, order_lines, order_amount):
        rewards = []
        data = OrderLine.mapped(order_lines, 'subtotal')
        total_order_amount = sum(data)
        if self.operator == '=':
            if self.reward_type == 'discount_amount' and total_order_amount == self.total_invoice_amount:
                get_total_discount = -(self.fixed_discount)
                rewards.append(Reward(product_id=self.discount_product_id.id,
                                      qty=1,
                                      price=get_total_discount,
                                      promotion_id=self.id,
                                      account_id=self.account_id.id,
                                      description=f'Discount For Total Order is over 1000{self.discount_product_id.name}'))
            elif self.reward_type == 'percentage' and total_order_amount == self.total_invoice_amount:
                actual_get_percent = self.fixed_discount
                get_percentage_amount = -(total_order_amount * (actual_get_percent / 100))
                rewards.append(Reward(product_id=self.discount_product_id.id,
                                      qty=1,
                                      price=get_percentage_amount,
                                      promotion_id=self.id,
                                      account_id=self.account_id.id,
                                      description=(" Discount %s Percent Get Total Order Amount is Over %s" % (
                                          self.fixed_discount, self.total_invoice_amount))))
            elif self.reward_type == 'foc_product' and total_order_amount == self.total_invoice_amount:
                foc_product_id = self.discount_product_id.id
                product_id = self.env['product.product'].browse(foc_product_id)
                uom = product_id.multi_uom_line_ids.filtered(lambda l: l.is_default_uom == True).id

                product_qty = self.product_qty
                rewards.append(Reward(product_id=foc_product_id,
                                      multi_uom_line_id=uom,
                                      qty=product_qty,
                                      price=0,
                                      promotion_id=self.id,
                                      account_id=self.account_id.id,
                                      description=(" Discount Free Product(FOC) Get Total Order is Over  %s" % (
                                          self.total_invoice_amount))))
            else:
                pass
        else:
            if self.reward_type == 'discount_amount' and total_order_amount >= self.total_invoice_amount:
                get_total_discount = - self.fixed_discount
                rewards.append(Reward(product_id=self.discount_product_id.id,
                                      qty=1,
                                      price=get_total_discount,
                                      promotion_id=self.id,
                                      account_id=self.account_id.id,
                                      description=f'Discount For Total Order is over 1000{self.discount_product_id.name}'))
            elif self.reward_type == 'percentage' and total_order_amount >= self.total_invoice_amount:
                get_percentage_amount = -(total_order_amount * (self.fixed_discount / 100))
                rewards.append(Reward(product_id=self.discount_product_id.id,
                                      qty=1,
                                      price=get_percentage_amount,
                                      promotion_id=self.id,
                                      account_id=self.account_id.id,
                                      description=(" Discount %s Percent Get Total Order Amount is Over %s" % (
                                          self.fixed_discount, self.total_invoice_amount))))
            elif self.reward_type == 'foc_product' and total_order_amount >= self.total_invoice_amount:
                foc_product_id = self.discount_product_id.id
                product_id = self.env['product.product'].browse(foc_product_id)
                uom = product_id.multi_uom_line_ids.filtered(lambda l: l.is_default_uom == True).id
                product_qty = self.product_qty
                rewards.append(Reward(product_id=foc_product_id,
                                      multi_uom_line_id=uom,
                                      qty=product_qty,
                                      price=0,
                                      promotion_id=self.id,
                                      account_id=self.account_id.id,
                                      description=(" Discount Free Product(FOC) Get Total Order is Over  %s" % (
                                          self.total_invoice_amount))))
            else:
                pass
        return rewards

    @api.onchange('reward_type')
    def onchange_reward_type(self):
        for rec in self:
            if rec.reward_type == 'foc_product':
                product_ids = self.env['product.product'].search([('detailed_type', '!=', 'service')])
                return {'domain': {'discount_product_id': [('id', 'in', product_ids.ids)]}}
            else:
                domain = [('detailed_type', '=', 'service')]
                service_product_ids = self.env['product.product'].search(domain)
                return {'domain': {'discount_product_id': [('id', 'in', service_product_ids.ids)]}}


class BuyOneGetOneLine(models.Model):
    _name = 'buy.one.get.one.line'
    _description = 'Buy One Get One Line'

    product_x_id = fields.Many2one('product.product', domain=[('available_in_pos', '=', True)], string='Product(X)')
    product_x_qty = fields.Float('Product X Qty', default=1)
    operator = fields.Selection(OPERATOR, 'Operator', default='=')
    product_y_id = fields.Many2one('product.product', domain=[('available_in_pos', '=', True)], string='Product(Y)')
    product_y_qty = fields.Float('Product Y Qty', default=1)
    account_id = fields.Many2one('account.account', 'COA')
    promotion_id = fields.Many2one('promotion.program', 'Promotion', ondelete='cascade')

    _sql_constraints = [
        ('product_x_qty_greater_than_zero', 'CHECK(product_x_qty > 0)', 'Product(X) qty has to be greater than zero.'),
        ('product_y_qty_greater_than_zero', 'CHECK(product_y_qty > 0)', 'Product(Y) qty has to be greater than zero.')
    ]
