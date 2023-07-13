from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.http import request
from odoo.tools.safe_eval import pytz, datetime


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', store=True)
    hide_picking_type = fields.Boolean('Hide Picking Type')

    allow_analytic_account_ids = fields.Many2many('account.analytic.account', string='Analytic Accounts',
                                                  related='login_employee_id.allow_analytic_account_id')

    @api.model
    def _create_picking_from_pos_order_lines(self, location_dest_id, lines, picking_type, partner=False, session=False):
        """We'll create some picking based on order_lines"""
        if not session:
            session = self.env['pos.session']

        pickings = self.env['stock.picking']
        stockable_lines = lines.filtered(
            lambda l: l.product_id.type in ['product', 'consu'] and not float_is_zero(l.qty,
                                                                                      precision_rounding=l.product_id.uom_id.rounding))
        if not stockable_lines:
            return pickings
        positive_lines = stockable_lines.filtered(lambda l: l.qty > 0)
        negative_lines = stockable_lines - positive_lines

        if positive_lines:
            location_id = picking_type.default_location_src_id.id
            picking_vals = self._prepare_picking_vals(partner, picking_type, location_id, location_dest_id)
            picking_vals.update({
                'pos_session_id': session.id,
                'analytic_account_id': session.analytic_account_id.id,
            })
            positive_picking = self.env['stock.picking'].create(picking_vals)

            positive_picking._create_move_from_pos_order_lines(positive_lines)
            try:
                with self.env.cr.savepoint():
                    positive_picking._action_done()
            except (UserError, ValidationError):
                pass

            pickings |= positive_picking
        if negative_lines:
            if picking_type.return_picking_type_id:
                return_picking_type = picking_type.return_picking_type_id
                return_location_id = return_picking_type.default_location_dest_id.id
            else:
                return_picking_type = picking_type
                return_location_id = picking_type.default_location_src_id.id

            picking_vals = self._prepare_picking_vals(partner, picking_type, location_dest_id, return_location_id)
            picking_vals.update({
                'pos_session_id': session.id,
                'analytic_account_id': session.analytic_account_id.id,
            })
            negative_picking = self.env['stock.picking'].create(picking_vals)
            negative_picking._create_move_from_pos_order_lines(negative_lines)
            try:
                with self.env.cr.savepoint():
                    negative_picking._action_done()
            except (UserError, ValidationError):
                pass
            pickings |= negative_picking
        return pickings

    def _prepare_stock_move_vals(self, first_line, order_lines):
        return {
            'name': first_line.name,
            'product_uom': first_line.product_id.uom_id.id,
            'picking_id': self.id,
            'picking_type_id': self.picking_type_id.id,
            'product_id': first_line.product_id.id,
            'analytic_account_id': first_line.analytic_account_id.id,
            'product_uom_qty': abs(sum(order_lines.mapped('qty'))),
            'state': 'draft',
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'company_id': self.company_id.id,
        }

    def _action_done(self):
        res = super(StockPicking, self)._action_done()
        analytic_account_id = self.analytic_account_id.id
        if not analytic_account_id:
            return res
        stock_moves = self.move_lines.ids
        account_moves = self.env['account.move'].search([('stock_move_id', 'in', stock_moves)])
        for account_move in account_moves:
            account_move.write({'analytic_account_id': analytic_account_id})
        return res

    @api.model
    def default_get(self, fields_list):
        vals = super(StockPicking, self).default_get(fields_list)
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




class StockMove(models.Model):
    _inherit = 'stock.move'

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')

    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id,
                                  cost):
        self.ensure_one()
        AccountMove = self.env['account.move'].with_context(default_journal_id=journal_id)

        move_lines = self._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id, description)
        if move_lines:
            date = self._context.get('force_period_date', False)
            print('Acc Date', date)
            if not date and self.picking_id:
                picking_date = self.picking_id.scheduled_date

                local_tz_st = pytz.timezone(self.env.user.tz or 'UTC')
                if picking_date:
                    scheduled_date_only = picking_date
                    start_d = scheduled_date_only.replace(tzinfo=pytz.utc).astimezone(local_tz_st)
                    start_date = datetime.strftime(start_d, DEFAULT_SERVER_DATETIME_FORMAT)
                    scheduled_date_only = datetime.strptime(
                        start_date, '%Y-%m-%d %H:%M:%S'
                    )
                    date = scheduled_date_only.date()

                    print('Date', date)
            if not date and self.date:
                picking_date = self.date

                local_tz_st = pytz.timezone(self.env.user.tz or 'UTC')
                if picking_date:
                    scheduled_date_only = picking_date
                    start_d = scheduled_date_only.replace(tzinfo=pytz.utc).astimezone(local_tz_st)
                    start_date = datetime.strftime(start_d, DEFAULT_SERVER_DATETIME_FORMAT)
                    scheduled_date_only = datetime.strptime(
                        start_date, '%Y-%m-%d %H:%M:%S'
                    )
                    date = scheduled_date_only.date()

            new_account_move = AccountMove.sudo().create({
                'journal_id': journal_id,
                'line_ids': move_lines,
                'date': date,
                'ref': description,
                'analytic_account_id': self.analytic_account_id.id,
                'stock_move_id': self.id,
                'stock_valuation_layer_ids': [(6, None, [svl_id])],
                'move_type': 'entry',
            })
            new_account_move._post()


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account',
                                          related='move_id.analytic_account_id', store=True)
    origin = fields.Char(related='move_id.origin', string='Source', store=True)
