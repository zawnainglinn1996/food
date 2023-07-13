# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo.exceptions import UserError
from odoo import api, fields, models, _
from odoo.http import request


class StockRepackaging(models.Model):
    _name = "stock.repackaging"
    _order = "id desc"
    _description = "Product Repackaging"

    @api.model
    def _default_dest_location_id(self):
        location_obj = self.env['stock.location']
        stock_location_id = location_obj.search([('name', '=',
                                                  'Virtual Locations')])
        location_id = None
        if stock_location_id:
            location_id = location_obj.search([('is_repackaging', '=', True)])
            if location_id:
                if len(location_id) > 1:
                    raise UserError(
                        _("Repackaging location must have  the one location."))
            if not location_id:
                location_id = location_obj.create({
                    'name':
                        'Repackaging',
                    'location_id':
                        stock_location_id.id,
                    'usage':
                        'inventory',
                    'is_repackaging':
                        True,
                })
            return location_id

    name = fields.Char('Repackaging Reference',
                       default="New",
                       readonly=True,
                       store=True)
    location_id = fields.Many2one("stock.location",
                                  "Locations",
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
    stockrepackagingline_id = fields.One2many("stock.repackaging.line",
                                              "repackaging_id",
                                              "Stock Repackaging Lines")
    company_id = fields.Many2one('res.company',
                                 'Company',
                                 readonly=True,
                                 index=True,
                                 required=True,
                                 states={'draft': [('readonly', False)]},
                                 default=lambda self: self.env['res.company'].
                                 _company_default_get('stock.repackaging'))
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Repackage'),
                              ('done', 'Done')],
                             "Status",
                             default="draft")
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')

    def action_done(self):
        self._action_done()
        self.stockrepackagingline_id.move_id.write({'date': self.date})
        self.stockrepackagingline_id.move_id.move_line_ids.write({'date': self.date})
        for line in self.stockrepackagingline_id.move_id:
            valuation = self.env['stock.valuation.layer'].search([('stock_move_id', '=', line.id)])
            valuation.write({'date': self.date})
        self.write({'state': 'done'})

    def _action_done(self):
        self.get_move_line_value()

    def get_move_line_value(self):
        for package in self.filtered(lambda x: x.state not in ('done')):
            for line in self.stockrepackagingline_id:
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
                    'name': _(line.repackaging_id.name or ''),
                    'product_id': line.product_id.id,
                    'product_uom': line.uom_id.id,
                    'analytic_account_id': line.repackaging_id.analytic_account_id.id,
                    'product_uom_qty': qty,
                    'date': line.repackaging_id.date,
                    'company_id': line.env.user.company_id.id,
                    'price_unit': line.unit_cost,
                    'state': 'confirmed',
                    'location_id': line.location_id.id,
                    'location_dest_id': line.dest_location_id.id,
                    'stock_repackaging_line_id': line.id,
                    'move_line_ids': [(0, 0, {'product_id': line.product_id.id,
                                              'product_uom_qty': 0,
                                              'product_uom_id': line.uom_id.id,
                                              'date': line.repackaging_id.date,
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
        for line in self.stockrepackagingline_id:
            if line.product_id.child_id:
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
        if self.stockrepackagingline_id:
            for line in self.stockrepackagingline_id:
                if not line.is_repackage:
                    line.unlink()
        self.write({'state': 'draft'})

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('stock.repackaging') or 'New'
        if vals.get('location') == False:
            vals['location'] = True
        result = super(StockRepackaging, self).create(vals)
        return result

    def btn_show_product_moves(self):
        return {
            'name': 'Product Moves',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.move.line',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.stockrepackagingline_id.move_id.move_line_ids.ids)],
        }

    def btn_show_valuations(self):
        action = self.env["ir.actions.actions"]._for_xml_id("stock_account.stock_valuation_layer_action")
        action['domain'] = [('stock_move_id', 'in', self.stockrepackagingline_id.move_id.ids)]
        return action

    def unlink(self):
        if any(pack.state not in ('draft') for pack in self):
            raise UserError(_('You can only delete in draft state.'))
        return super(StockRepackaging, self).unlink()



    @api.model
    def default_get(self, fields_list):
        vals = super(StockRepackaging, self).default_get(fields_list)
        default_analytic_account_id = False
        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])
            if employee_id:
                analytic_id = employee_id.def_analytic_account_id.id
                if analytic_id:
                    default_analytic_account_id = analytic_id
        if default_analytic_account_id:
            vals.update({'analytic_account_id': default_analytic_account_id})
        return vals

    @api.onchange('analytic_account_id')
    def onchange_login_employee(self):
        for rec in self:
            if request.session.emp_id:
                data = int(request.session.emp_id)
                employee_id = self.env['hr.employee'].search([('id', '=', data)])

                if employee_id:
                    analytic_ids = employee_id.allow_analytic_account_id.ids
                    return {'domain': {'analytic_account_id': [('id', 'in', analytic_ids)]}}
            else:
                return {'domain': {'analytic_account_id': []}}


    # PDF
    def get_repackaging_pdf(self):
        records = []
        lines = []
        for rec in self:
            for line in rec.stockrepackagingline_id:
                onhand = '0.00'
                qty = '0.00'
                balance = '0.00'
                code = ''
                if line.onhand_qty:
                    onhand = '{0:,.2f}'.format(line.onhand_qty)
                if line.quantity:
                    qty = '{0:,.2f}'.format(line.quantity)
                if line.balance:
                    balance = '{0:,.2f}'.format(line.balance)
                if line.product_id:
                    if line.product_id.default_code:
                        code = line.product_id.default_code
                lines.append({
                    'code': code,
                    'name': line.name or '',
                    'onhand': onhand,
                    'qty': qty,
                    'balance': balance,
                    'uom': line.uom_id.name if line.uom_id else '',
                    'cost': '{0:,.2f}'.format(line.unit_cost) if line.unit_cost else '0.00',
                    'amount': '{0:,.2f}'.format(line.amount) if line.amount else '0.00',
                })
            records.append({
                'ref': rec.name or '',
                'location': rec.location_id.complete_name or '',
                'date': (rec.date + timedelta(hours=6, minutes=30)).strftime("%d-%m-%Y %H:%M:%S"),
                'lines': lines,
            })
            return self.env.ref('repackaging.action_repacking_report').report_action(self, data={
                'records': records,
            })



class StockRepackingLine(models.Model):
    _name = "stock.repackaging.line"
    _order = 'sequence_number'
    _description = "Stock Repackaging Line"

    def _default_location_id(self):
        if self.repackaging_id:
            return self.repackaging_id.location_id

    def _default_dest_location_id(self):
        if self.repackaging_id:
            return self.repackaging_id.destination_location_id

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
    repackaging_id = fields.Many2one("stock.repackaging",
                                     "Repackage",
                                     ondelete='cascade',
                                     index=True,
                                     store=True)
    is_repackage = fields.Boolean("Repackage?", default=True)
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
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account',
                                          related='repackaging_id.analytic_account_id', store=True)

    def action_get_stock_move_lines(self):
        action = self.env.ref('stock.stock_move_line_action').read([])[0]
        action['domain'] = [('move_id', '=', self.move_id.id)]
        return action

    @api.depends('product_id', 'onhand_qty', 'unit_cost', 'quantity',
                 'balance')
    def _compute_amount(self):
        for rec in self:
            rec.amount = 0
            rec.balance = 0
            rec.onhand_qty = rec.onhand_qty
            equ_qty = 0
            if rec.is_repackage and rec.product_id:
                rec.unit_cost = rec.product_id.standard_price
            else:
                if not rec.unit_cost and rec.product_id:
                    product_id = rec.env['product.template'].search([
                        ('child_id', '=', rec.product_id.id)
                    ])
                    if product_id.equvalent_qty < 0:
                        equ_qty = (-1) * product_id.equvalent_qty
                        rec.unit_cost = round(product_id.standard_price * equ_qty,
                                              2)
                    else:
                        rec.unit_cost = round(
                            product_id.standard_price / product_id.equvalent_qty,
                            2)
            amount = round(rec.unit_cost * rec.quantity, 2)
            rec.amount = amount
            if not rec.onhand_qty:
                if rec.product_id:
                    stock_quant_ids = rec.env['stock.quant'].search([
                        ('product_id', '=', rec.product_id.id),
                        ('location_id', '=', rec.repackaging_id.location_id.id)
                    ])
                    if stock_quant_ids:
                        rec.onhand_qty = stock_quant_ids.quantity

            rec.balance = rec.onhand_qty + rec.quantity
            if rec.repackaging_id:
                if not rec.dest_location_id:
                    if rec.repackaging_id.destination_location_id:
                        rec.dest_location_id = rec.repackaging_id.destination_location_id.id
                if not rec.location_id:
                    if rec.repackaging_id.location_id:
                        rec.location_id = rec.repackaging_id.location_id.id

    @api.model
    def create(self, values):
        res = super(StockRepackingLine, self).create(values)
        return res

    def copy(self, default=None):
        default = dict(default or {})
        if self.product_id.child_id:
            product_id = self.product_id.child_id
            default['name'] = product_id.name
            default['product_id'] = product_id.id
            onhand = product_id.qty_available
            if product_id:
                stock_quant_ids = self.env['stock.quant'].search([
                    ('product_id', '=', product_id.id),
                    ('location_id', '=',
                     self.repackaging_id.destination_location_id.id)
                ])
                if stock_quant_ids:
                    onhand = stock_quant_ids.quantity
            default['onhand_qty'] = - onhand
            if self.product_id.equvalent_qty < 0:
                default['quantity'] = self.quantity / self.product_id.equvalent_qty
            else:
                default['quantity'] = (-1) * self.quantity * self.product_id.equvalent_qty

            default['balance'] = default['onhand_qty'] + default['quantity']

            if self.is_repackage:
                default['is_repackage'] = False

            if self.product_id.equvalent_qty > 0:
                default['unit_cost'] = self.unit_cost / self.product_id.equvalent_qty
            elif self.product_id.equvalent_qty < 0:
                default['unit_cost'] = self.unit_cost / self.product_id.equvalent_qty
            else:
                UserError(
                    _("Please set sub equvalent quantity of sub product."))
            default['amount'] = default['quantity'] * default['unit_cost']
            if self.repackaging_id:
                if self.repackaging_id.destination_location_id:
                    default['location_id'] = self.repackaging_id.destination_location_id.id
                if self.repackaging_id.location_id:
                    default['dest_location_id'] = self.repackaging_id.location_id.id
        return super(StockRepackingLine, self).copy(default)

    def post_inventory(self):
        # The inventory is posted as a single step which means quants cannot be moved from an internal location to another using an inventory
        # as they will be moved to inventory loss, and other quants will be created to the encoded quant location. This is a normal behavior
        # as quants cannot be reuse from inventory location (users can still manually move the products before/after the inventory if they want).
        self.mapped('move_id').filtered(
            lambda move: move.state != 'done')._action_done()


class Location(models.Model):
    _inherit = "stock.location"

    is_repackaging = fields.Boolean("Is Repackaging", default=False)


class StockMove(models.Model):
    _inherit = 'stock.move'

    stock_repackaging_line_id = fields.Many2one('stock.repackaging.line', 'Packaging Line')
