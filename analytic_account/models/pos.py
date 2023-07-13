from odoo import api, models, fields, _


class PosConfig(models.Model):
    _inherit = 'pos.config'

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')


class PosSession(models.Model):
    _inherit = 'pos.session'

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account',
                                          compute='compute_analytic_account_id', store=True)

    @api.depends('config_id')
    def compute_analytic_account_id(self):
        for rec in self:
            rec.analytic_account_id = False
            pos_config = rec.config_id
            if pos_config:
                rec.analytic_account_id = pos_config.analytic_account_id.id

    def _create_picking_at_end_of_session(self):
        self.ensure_one()
        lines_grouped_by_dest_location = {}
        picking_type = self.config_id.picking_type_id

        if not picking_type or not picking_type.default_location_dest_id:
            session_destination_id = self.env['stock.warehouse']._get_partner_locations()[0].id
        else:
            session_destination_id = picking_type.default_location_dest_id.id

        for order in self.order_ids:
            if order.company_id.anglo_saxon_accounting and order.to_invoice:
                continue
            destination_id = order.partner_id.property_stock_customer.id or session_destination_id
            if destination_id in lines_grouped_by_dest_location:
                lines_grouped_by_dest_location[destination_id] |= order.lines
            else:
                lines_grouped_by_dest_location[destination_id] = order.lines

        for location_dest_id, lines in lines_grouped_by_dest_location.items():
            pickings = self.env['stock.picking']._create_picking_from_pos_order_lines(location_dest_id, lines,
                                                                                      picking_type, session=self)

            pickings.write({
                'pos_session_id': self.id,
                'origin': self.name,

            })

    def action_pos_session_open(self):
        # second browse because we need to refetch the data from the DB for cash_register_id
        # we only open sessions that haven't already been opened
        for session in self.filtered(lambda session: session.state == 'opening_control'):
            values = {}
            if not session.start_at:
                values['start_at'] = fields.Datetime.now()
            if session.config_id.cash_control and not session.rescue:
                last_session = self.search([('config_id', '=', session.config_id.id), ('id', '!=', session.id)],
                                           limit=1)
                session.cash_register_id.balance_start = last_session.cash_register_id.balance_end_real if last_session else 0
                session.cash_register_id.analytic_account_id = last_session.analytic_account_id.id
                values['state'] = 'opening_control'
            else:
                values['state'] = 'opened'
            session.write(values)
        return True

    def _validate_session(self, balancing_account=False, amount_to_balance=0, bank_payment_method_diffs=None):
        res = super(PosSession, self)._validate_session(balancing_account, amount_to_balance, bank_payment_method_diffs)
        statement = self.cash_register_id
        picking_ids = self.env['stock.picking'].search([('pos_session_id', '=', self.id)])
        picking_ids.move_lines.stock_valuation_layer_ids.write({
            'analytic_account_id': self.analytic_account_id.id
        })
        if not self.config_id.cash_control:
            statement.write({'balance_end_real': statement.balance_end,
                             'analytic_account_id': self.analytic_account_id.id
                             })

        return res

    def _create_account_move(self, balancing_account=False, amount_to_balance=0, bank_payment_method_diffs=None):
        """ Create account.move and account.move.line records for this session.

        Side-effects include:
            - setting self.move_id to the created account.move record
            - creating and validating account.bank.statement for cash payments
            - reconciling cash receivable lines, invoice receivable lines and stock output lines
        """
        journal = self.config_id.journal_id
        # Passing default_journal_id for the calculation of default currency of account move
        # See _get_default_currency in the account/account_move.py.
        account_move = self.env['account.move'].with_context(default_journal_id=journal.id).create({
            'journal_id': journal.id,
            'date': fields.Date.context_today(self),
            'ref': self.name,
            'analytic_account_id': self.analytic_account_id.id,
        })
        self.write({'move_id': account_move.id})

        data = {'bank_payment_method_diffs': bank_payment_method_diffs or {}}
        data = self._accumulate_amounts(data)
        data = self._create_non_reconciliable_move_lines(data)
        data = self._create_bank_payment_moves(data)
        data = self._create_pay_later_receivable_lines(data)
        data = self._create_cash_statement_lines_and_cash_move_lines(data)
        data = self._create_invoice_receivable_lines(data)
        data = self._create_stock_output_lines(data)
        if balancing_account and amount_to_balance:
            data = self._create_balancing_line(data, balancing_account, amount_to_balance)

        return data


class PosOrder(models.Model):
    _inherit = 'pos.order'

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account',
                                          compute='compute_analytic_account_id', store=True)

    @api.depends('session_id')
    def compute_analytic_account_id(self):
        for rec in self:
            rec.analytic_account_id = False
            session = rec.session_id
            if session:
                rec.analytic_account_id = session.analytic_account_id.id

    def _create_order_picking(self):
        self.ensure_one()
        if not self.session_id.update_stock_at_closing or (self.company_id.anglo_saxon_accounting and self.to_invoice):
            picking_type = self.config_id.picking_type_id
            if self.partner_id.property_stock_customer:
                destination_id = self.partner_id.property_stock_customer.id
            elif not picking_type or not picking_type.default_location_dest_id:
                destination_id = self.env['stock.warehouse']._get_partner_locations()[0].id
            else:
                destination_id = picking_type.default_location_dest_id.id
            pickings = self.env['stock.picking']._create_picking_from_pos_order_lines(destination_id, self.lines,
                                                                                      picking_type, self.partner_id,
                                                                                      self.session_id)

            pickings.move_lines.stock_valuation_layer_ids.write({
                'analytic_account_id': self.analytic_account_id.id
            })
            pickings.write(
                {'pos_session_id': self.session_id.id,
                 'pos_order_id': self.id,
                 'origin': self.name,
                 })

    def _prepare_invoice_vals(self):
        res = super(PosOrder, self)._prepare_invoice_vals()
        res.update({
            'analytic_account_id': self.analytic_account_id.id,
        })
        return res


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account',
                                          related='order_id.analytic_account_id')


class PosOrderReport(models.Model):
    _inherit = "report.pos.order"

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', related=False)

    def _select(self):
        return super(PosOrderReport, self)._select() + ',ps.analytic_account_id AS analytic_account_id'

    def _group_by(self):
        return super(PosOrderReport, self)._group_by() + ',ps.analytic_account_id'


class PosPayment(models.Model):
    _inherit = "pos.payment"

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account',
                                          compute="compute_analytic_account")

    @api.depends("session_id")
    def compute_analytic_account(self):
        for record in self:
            session = False
            if record.session_id:
                session = self.env['pos.session'].search([('id', '=', record.session_id.id)], limit=1)
            else:
                session = False
            if session:
                record.analytic_account_id = session.analytic_account_id
            else:
                record.analytic_account_id = False
