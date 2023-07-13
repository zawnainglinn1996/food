import math

from odoo import api, models, fields
from odoo.exceptions import UserError
from odoo.http import request

class StockPackaging(models.Model):

    _name = 'stock.packaging'
    _description = 'Stock Packaging'


    name = fields.Char('Name', default='New', required=1, copy=False)
    date = fields.Datetime('Date', default=fields.Datetime.now, required=1)
    location_id = fields.Many2one('stock.location', 'Location', domain=[('usage', '=', 'internal')], required=1)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    line_ids = fields.One2many('stock.packaging.line', 'stock_package_id', 'Lines')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Confirmed'),
                              ('done', 'Done')], default='draft')


    def btn_package(self):
        sequence = 1
        for line in self.line_ids:
            if line.qty >= 0:
                raise UserError('The sign of the quantities of child product must be minus.')
            line.sequence = sequence
            sequence += 1
            parent_product = line.product_id.parent_product_id
            parent_qty = math.floor(abs(line.qty) / line.product_id.child_product_qty)
            parent_unit_cost = line.unit_cost * line.product_id.child_product_qty
            parent_total_cost = parent_unit_cost * parent_qty
            self.env['stock.packaging.line'].create({
                'sequence': sequence,
                'product_id': parent_product.id,
                'qty': parent_qty,
                'unit_cost': parent_unit_cost,
                'total_cost': parent_total_cost,
                'stock_package_id': self.id,
                'parent_line_id': line.id,
            })
            sequence += 1
        values = {'state': 'confirm'}
        if not self.name or self.name == 'New':
            sequence = self.env['ir.sequence'].sudo().search([('code', '=', 'stock.packaging.sequence'),
                                                              ('company_id', '=', self.company_id.id)], limit=1)
            ref = sequence.next_by_id()
            values['name'] = ref
        self.write(values)

    def btn_set_to_draft(self):
        self.line_ids.filtered(lambda l: l.parent_line_id).unlink()
        self.write({'state': 'draft'})

    def btn_validate(self):
        internal_loc = self.location_id
        inventory_loc = self.company_id.package_location_id
        if not inventory_loc:
            raise UserError('Please configure packaging location in Settings >> Inventory >> Packaging.')
        insufficient_products = []
        stock_move_values = []
        for line in self.line_ids:
            if not self.env.context.get('do_it_anyway') and \
                    not line.parent_line_id and \
                    line.available_qty < abs(line.qty):
                insufficient_products.append((0, 0, {
                    'product_id': line.product_id.id,
                    'required_qty': abs(line.qty),
                    'current_qty': line.available_qty,
                }))
                continue
            if line.parent_line_id:
                stock_move_values.append(line._prepare_stock_move_values(inventory_loc, internal_loc))
            else:
                stock_move_values.append(line._prepare_stock_move_values(internal_loc, inventory_loc))
        if insufficient_products:
            return self.show_insufficient_warning(insufficient_products)
        moves = self.env['stock.move'].create(stock_move_values)
        moves.with_context(force_period_date=self.date)._action_done()
        self.line_ids.move_ids.write({'date': self.date})
        self.line_ids.move_ids.move_line_ids.write({'date': self.date})
        for line in self.line_ids.move_ids:
            valuation = self.env['stock.valuation.layer'].search([('stock_move_id', '=', line.id)])
            valuation.write({'date': self.date})
        self.write({'state': 'done'})

    def show_insufficient_warning(self, insufficient_products):
        context = dict(self.env.context)
        context.update({
            'default_packing_id': self.id,
            'default_line_ids': insufficient_products,
        })
        return {
            'name': 'Insufficient Warning',
            'type': 'ir.actions.act_window',
            'res_model': 'show.insufficient.qty',
            'view_mode': 'form',
            'target': 'new',
            'context': context,
        }

    def btn_show_product_moves(self):
        return {
            'name': 'Product Moves',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.move.line',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.line_ids.move_ids.move_line_ids.ids)],
        }

    def btn_show_valuations(self):
        action = self.env["ir.actions.actions"]._for_xml_id("stock_account.stock_valuation_layer_action")
        action['domain'] = [('stock_move_id', 'in', self.line_ids.move_ids.ids)]
        return action

    def unlink(self):
        for rec in self:
            if rec.state == 'done':
                raise UserError('You can\'t delete records which are in done stage.')
        return super(StockPackaging, self).unlink()

    @api.model
    def default_get(self, fields_list):
        vals = super(StockPackaging, self).default_get(fields_list)
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


class StockPackagingLine(models.Model):

    _name = 'stock.packaging.line'
    _description = 'Stock Packaging Line'

    sequence = fields.Integer('Sequence')
    product_id = fields.Many2one('product.product', 'Product', required=1)
    product_name = fields.Char('Product Name', related='product_id.name', store=True)
    qty = fields.Float('Qty')
    available_qty = fields.Float('Available Qty', compute='_compute_available_qty', store=True)
    forecasted_qty = fields.Float('Forecasted Qty', compute='_compute_forecast_qty', store=True)
    unit_cost = fields.Float('Unit Cost')
    total_cost = fields.Float('Total Cost', compute='_compute_total_cost', store=True)
    stock_package_id = fields.Many2one('stock.packaging', 'Package', ondelete='cascade')
    move_ids = fields.One2many('stock.move', 'stock_packaging_line_id', 'Move Lines')
    parent_line_id = fields.Many2one('stock.packaging.line', 'Parent Line')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.qty = self.product_id.child_product_qty * -1
        self.unit_cost = self.product_id.standard_price

    @api.depends('qty', 'unit_cost')
    def _compute_total_cost(self):
        for rec in self:
            rec.total_cost = rec.unit_cost * rec.qty

    @api.depends('qty', 'available_qty')
    def _compute_forecast_qty(self):
        for rec in self:
            rec.forecasted_qty = rec.available_qty + rec.qty

    @api.depends('product_id', 'stock_package_id.location_id')
    def _compute_available_qty(self):
        for rec in self:
            product = rec.product_id
            location = rec.stock_package_id.location_id
            if not (product and location):
                rec.available_qty = 0
                continue
            quants = self.env['stock.quant']._gather(product, location)
            rec.available_qty = sum(quants.mapped('available_quantity'))

    def _prepare_stock_move_values(self, src_loc, dest_loc):
        vals = {
            'name': f'{self.stock_package_id.name}-{self.product_id.name}',
            'location_id': src_loc.id,
            'location_dest_id': dest_loc.id,
            'product_id': self.product_id.id,
            'product_uom_qty': abs(self.qty),
            'product_uom': self.product_id.uom_id.id,
            'reference': self.stock_package_id.name,
            'company_id': self.stock_package_id.company_id.id,
            'stock_packaging_line_id': self.id,
            'date': self.stock_package_id.date,
            'analytic_account_id': self.stock_package_id.analytic_account_id.id,
            'move_line_ids': [(0, 0, {
                'product_id': self.product_id.id,
                'product_uom_qty': 0,
                'product_uom_id': self.product_id.uom_id.id,
                'qty_done': abs(self.qty),
                'date': self.stock_package_id.date,
                'location_id': src_loc.id,
                'location_dest_id': dest_loc.id,
            })],
            'state': 'draft',
        }
        return vals
