# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo import api, fields, models, _


class StockConversion(models.Model):
    _name = "stock.conversion"
    _order = "id desc"
    _description = "Product Conversion"

    @api.model
    def _default_dest_location_id(self):
        location_obj = self.env['stock.location']
        stock_location_id = location_obj.search([('name', '=',
                                                  'Virtual Locations')])
        location_id = None
        if stock_location_id:
            location_id = location_obj.search([('is_unit', '=', True)])
            if location_id:
                if len(location_id) > 1:
                    raise UserError(
                        _("Repackaging location must have  the one location."))
            if not location_id:
                location_id = location_obj.create({
                    'name': 'Unit Conversion',
                    'location_id': stock_location_id.id,
                    'usage': 'inventory',
                    'is_unit': True,
                })
            return location_id

    @api.model
    def _default_location_id(self):
        company_user = self.env.user.company_id
        warehouse = self.env['stock.warehouse'].search(
            [('company_id', '=', company_user.id)], limit=1)
        if warehouse:
            return warehouse.lot_stock_id.id
        else:
            raise UserError(
                _('You must define a warehouse for the company: %s.') %
                (company_user.name, ))

    name = fields.Char('Unit Conversion Reference',
                       default="New",
                       readonly=True,
                       store=True)
    location_id = fields.Many2one("stock.location",
                                  "Locations",
                                  default=_default_location_id,
                                  required=True,
                                  store=True)
    location = fields.Boolean('location Readonly', default=False)
    destination_location_id = fields.Many2one(
        "stock.location",
        "Location",
        default=_default_dest_location_id,
        required=True,
        store=True)
    date = fields.Datetime("Date",
                       default=fields.Datetime.now,
                       required=True,
                       store=True)
    stockconversionline_id = fields.One2many("stock.conversion.line",
                                              "conversion_id",
                                              "Stock Conversion Lines")
    company_id = fields.Many2one('res.company',
                                 'Company',
                                 readonly=True,
                                 index=True,
                                 required=True,
                                 states={'draft': [('readonly', False)]},
                                 default=lambda self: self.env['res.company']._company_default_get('stock.repackaging'))
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Repackage'),
                              ('done', 'Done')],
                             "Status",
                             default="draft")
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')

    @api.onchange('location_id')
    def onchange_location_id(self):
        if self.location_id:
            self.analytic_account_id = self.location_id.analytic_account_id
        else:
            self.location_id = ''

    def action_done(self):
        self._action_done()
        self.write({'state': 'done'})

    def _action_done(self):
        self.get_move_line_value()

    def get_move_line_value(self):
        for package in self.filtered(lambda x: x.state not in ('done')):
            for line in self.stockconversionline_id:
                move_to = move_from = []
                qty = reqty = 0
                if line.quantity < 0:
                    qty = line.quantity * (-1)
                else:
                    qty = line.quantity
                if line.quantity >= 1:
                    reqty = line.quantity * (-1)
                else:
                    reqty = line.quantity
                val = {
                    'name': _(line.conversion_id.name or ''),
                    'product_id': line.product_id.id,
                    'product_uom': line.uom_id.id,
                    'product_uom_qty': qty,
                    'date': line.conversion_id.date,
                    'company_id': line.env.user.company_id.id,
                    'price_unit': line.unit_cost,
                    'state': 'confirmed',
                    'analytic_account_id': line.conversion_id.analytic_account_id.id,
                    'location_id': line.location_id.id,
                    'location_dest_id': line.dest_location_id.id,
                    'move_line_ids': [(0, 0, {'product_id':  line.product_id.id,
                                              'product_uom_qty': 0,
                                              'product_uom_id': line.uom_id.id,
                                              'date': line.conversion_id.date,
                                              'qty_done': qty,
                                              'location_id': line.location_id.id,
                                              'location_dest_id': line.dest_location_id.id,
                                              })]
                }
                move_id = self.env['stock.move'].create(val)
                line.post_inventory()
                move_id.with_context(force_period_date=self.date)._action_done()
                line.write({'move_id': move_id.id, 'state': 'done'})

    def action_confirm(self):
        num = 0
        for line in self.stockconversionline_id:
            if line.product_id.big_id:
                if line.quantity:
                    num += 1
                    line.write({'sequence_number': num})
                    copy_id = line.copy()
                    num += 1
                    copy_id.write({'sequence_number': num})
                else:
                    raise UserError(_("Product quantity is equal 0."))
            else:
                raise UserError(_("Repackage product does not exist."))
        self.write({'state': 'confirm'})

    def action_resettodraft(self):
        if self.stockconversionline_id:
            for line in self.stockconversionline_id:
                if not line.is_unit:
                    line.unlink()
        self.write({'state': 'draft'})

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('stock.conversion') or 'New'
        if vals.get('location') == False:
            vals['location'] = True
        result = super(StockConversion, self).create(vals)
        return result

    def unlink(self):
        if any(pack.state not in ('draft') for pack in self):
            raise UserError(_('You can only delete in draft state.'))
        return super(StockConversion, self).unlink()


class StockConversionLine(models.Model):
    _name = "stock.conversion.line"
    _order = 'sequence_number'
    _description = "Stock Conversion Line"

    def _default_location_id(self):
        if self.conversion_id:
            return self.conversion_id.location_id

    def _default_dest_location_id(self):
        if self.conversion_id:
            return self.conversion_id.destination_location_id

    name = fields.Char("Product Name",
                       related="product_id.name",
                       store=True,
                       readonly=True)
    product_id = fields.Many2one("product.product",
                                 "Internal Reference",
                                 readonly=False,
                                 store=True)
    onhand_qty = fields.Float("On Hand",
                              digits='Product Price',
                              readonly=True,
                              compute="_compute_amount",
                              store=True)
    quantity = fields.Float("Quantity", digits='Product Price', store=True)
    balance = fields.Float("Balance",
                           compute="_compute_amount",
                           readonly=True,
                           store=True)
    uom_id = fields.Many2one("uom.uom",
                             "UOM",
                             related="product_id.uom_id",
                             readonly=True,
                             store=True)
    unit_cost = fields.Float("Unit Cost",
                             compute="_compute_amount",
                             readonly=False,
                             digits='Product Price',
                             store=True)
    amount = fields.Float("Amount",
                          compute="_compute_amount",
                          digits='Product Price',
                          readonly=True,
                          store=True)
    conversion_id = fields.Many2one("stock.conversion",
                                     "Conversion",
                                     ondelete='cascade',
                                     index=True,
                                     store=True)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account',
                                          related='conversion_id.analytic_account_id', store=True)
    is_unit = fields.Boolean("Repackage?", default=True)
    location_id = fields.Many2one("stock.location",
                                  "Location",
                                  default=_default_location_id)
    dest_location_id = fields.Many2one("stock.location",
                                       "Destination Location",
                                       default=_default_dest_location_id)
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Package'),
                              ('done', 'Done')],
                             "Status",
                             default="draft")
    move_id = fields.Many2one("stock.move", "Stock Move")
    sequence_number = fields.Integer("No")

    def action_get_stock_move_lines(self):
        for res in self.move_id:
            res.date = self.conversion_id.date
            res.move_line_ids.date = self.conversion_id.date
        action = self.env.ref('stock.stock_move_line_action').read([])[0]
        action['domain'] = [('move_id', '=', self.move_id.id)]
        return action

    @api.depends('product_id', 'onhand_qty', 'unit_cost', 'quantity',
                 'balance')
    def _compute_amount(self):
        self.amount = 0
        self.balance = 0
        self.onhand_qty = self.onhand_qty
        equ_qty = 0
        if self.is_unit and self.product_id:
            self.unit_cost = self.product_id.standard_price
        else:
            if not self.unit_cost and self.product_id:
                product_id = self.env['product.template'].search([
                    ('big_id', '=', self.product_id.id)
                ])
                if product_id.big_equvalent_qty < 0:
                    equ_qty = (-1) * product_id.big_equvalent_qty
                    self.unit_cost = round(product_id.standard_price * equ_qty,
                                           2)
                else:
                    self.unit_cost = round(
                        product_id.standard_price / product_id.big_equvalent_qty,
                        2)
        amount = round(self.unit_cost * self.quantity, 2)
        self.amount = amount
        if not self.onhand_qty:
            if self.product_id:
                stock_quant_ids = self.env['stock.quant'].search([
                    ('product_id', '=', self.product_id.id),
                    ('location_id', '=', self.conversion_id.location_id.id)
                ])
                if stock_quant_ids:
                    self.onhand_qty = stock_quant_ids.quantity

        self.balance = self.onhand_qty + self.quantity
        if self.conversion_id:
            if not self.dest_location_id:
                if self.conversion_id.destination_location_id:
                    self.dest_location_id = self.conversion_id.destination_location_id.id
            if not self.location_id:
                if self.conversion_id.location_id:
                    self.location_id = self.conversion_id.location_id.id

    @api.model
    def create(self, values):
        res = super(StockConversionLine, self).create(values)
        return res

    def copy(self, default=None):
        default = dict(default or {})
        if self.product_id.big_id:
            product_id = self.product_id.big_id
            default['name'] = product_id.name
            default['product_id'] = product_id.id
            onhand = product_id.qty_available
            if product_id:
                stock_quant_ids = self.env['stock.quant'].search([
                    ('product_id', '=', product_id.id),
                    ('location_id', '=',
                     self.conversion_id.destination_location_id.id)
                ])
                if stock_quant_ids:
                    onhand = stock_quant_ids.quantity
            default['onhand_qty'] = - onhand
            if self.product_id.big_equvalent_qty < 0:
                default['quantity'] = self.quantity / self.product_id.big_equvalent_qty
            else:
                default['quantity'] = self.product_id.big_equvalent_qty

            default['balance'] = default['onhand_qty'] + default['quantity']
            if self.is_unit:
                default['is_unit'] = False
            if self.product_id.big_equvalent_qty > 0:
                default['unit_cost'] = (-1) * self.unit_cost * self.quantity
            elif self.product_id.big_equvalent_qty < 0:
                default['unit_cost'] = self.unit_cost / self.product_id.big_equvalent_qty
            else:
                UserError(
                    _("Please set sub equvalent quantity of sub product."))
            default['amount'] = default['quantity'] * default['unit_cost']
            if self.conversion_id:
                if self.conversion_id.destination_location_id:
                    default['location_id'] = self.conversion_id.destination_location_id.id
                if self.conversion_id.location_id:
                    default['dest_location_id'] = self.conversion_id.location_id.id
        return super(StockConversionLine, self).copy(default)

    def post_inventory(self):
        # The inventory is posted as a single step which means quants cannot be moved from an internal location to another using an inventory
        # as they will be moved to inventory loss, and other quants will be created to the encoded quant location. This is a normal behavior
        # as quants cannot be reuse from inventory location (users can still manually move the products before/after the inventory if they want).
        self.mapped('move_id').filtered(
            lambda move: move.state != 'done')._action_done()
