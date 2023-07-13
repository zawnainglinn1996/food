from time import strftime

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
from odoo.tools import float_round, float_compare
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class WholeSaleRequisition(models.Model):
    _name = 'whole.sale.requisition'
    _description = 'Whole Sale Requisition'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'reference_no'
    _order = 'created_date desc, id desc'

    def _get_location(self):
        to_location = self.env['stock.location'].search([('distribution_location', '=', True)], limit=1)
        return to_location

    def _get_approve_user(self):
        approve_user = self.env['res.users'].search([('sale_market_user', '=', True)], limit=1)
        return approve_user

    reference_no = fields.Char(string='Document No', readonly=1)
    created_date = fields.Datetime(string='Created Date', index=True, default=fields.Datetime.now, copy=False)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    active = fields.Boolean('Active',
                            help="If the active field is set to False, it will allow you to hide the account without removing it.",
                            default=True)
    state = fields.Selection(
        [('draft', 'Draft'),
         ('confirm', 'Confirmed'),
         ('approved', 'Approved'),
         ('cancel', 'Canceled')], string='State', default='draft', tracking=1)
    from_location_id = fields.Many2one('stock.location', string='From')
    to_location_id = fields.Many2one('stock.location', string='To', default=_get_location)
    # scheduled_date = fields.Date(string='Expected Date', default=fields.Date.context_today)
    scheduled_date = fields.Datetime(string='Expected Datetime', default=lambda self: fields.Datetime.now(), copy=False)

    is_whole_sale = fields.Boolean(string='Is a Whole Sale', default=False)
    is_retail_sale = fields.Boolean(string='Is a Retail Sale', default=False)
    requisition_line_ids = fields.One2many('whole.sale.requisition.line', 'requisition_id', string='Product Line',
                                           copy=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    req_by_sign = fields.Binary(string='Request Sign', help='For Req By Sign')
    req_by_name = fields.Many2one('hr.employee', string='Reuest Name', help='For Req By Name')
    req_by_position = fields.Char(string='Request Position', help='For Req By Position')

    approved_by_sign = fields.Binary(string='Approved Sign', help='for approved by sign')
    approved_by_name = fields.Many2one('hr.employee', string='Approved Name', help='For Approved by name')
    approved_by_position = fields.Char(string='Approved Position', help='For Approved By Position')

    confirm_by_sign = fields.Binary(string='Confirm Sign', help='For Confirm By Sign')
    confirm_by_name = fields.Many2one('hr.employee', string='Confirm Name', help='For Confirm By Name')
    confirm_by_position = fields.Char(string='Confirm Position', help='For Confirm By Position')

    deliver_by_sign = fields.Binary(string='Deliver Sign', help='For Delivery By Sign')
    deliver_by_name = fields.Many2one('hr.employee', string='Deliver Name ', help='Deliver BY Name')
    deliver_by_position = fields.Char(string='Deliver Position', help='For Deliver By Position')

    is_good_issued = fields.Boolean(string='Issued?', default='True')
    is_good_received = fields.Boolean(string='Received', default='True')

    picking_ids = fields.One2many('stock.picking', 'sale_requisition_id', string='Pickings')
    good_received_count = fields.Integer(string='Received ', compute='_compute_received_picking_ids', store=True)
    good_issued_count = fields.Integer(string='Issued', compute='_compute_issued_picking_ids', store=True)

    is_access_confirm = fields.Boolean('Access Confirm', compute='_check_access')
    is_access_approve = fields.Boolean('Access Approve', compute='_check_access')
    is_access_cancel = fields.Boolean('Access Cancel', compute='_check_access')

    allow_analytic_account_id = fields.Many2many('account.analytic.account', string='Analytic Accounts',
                                                 related='login_employee_id.allow_analytic_account_id')

    def _check_access(self):
        self.is_access_confirm = self.is_access_approve = self.is_access_cancel = False
        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])
            if employee_id:
                if employee_id.is_sale_req_confirm:
                    self.is_access_confirm = True
                if employee_id.is_sale_req_approve:
                    self.is_access_approve = True
                if employee_id.is_sale_req_cancel:
                    self.is_access_cancel = True

    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    sale_type = fields.Selection([
        ('whole_sale', 'Whole Sale'),
        ('retail_sale', 'Retail Sale'),
    ], string='Sale Type', readonly=True, compute='get_sale_type', store=True)

    sale_picking = fields.Selection([
        ('delivery', 'Delivery'),
        ('pickup', 'Pickup'),
    ], string='Picking Type', readonly=True, compute=None)

    partner_id = fields.Many2one('res.partner', string='Customer Name')
    user_id = fields.Many2one('res.users', string='To Approve', tracking=True, default=_get_approve_user)

    is_picking_done = fields.Boolean(string='Is Picking Done', compute='get_picking_status', copy=False)
    is_first_picking = fields.Boolean(string='First Picking', default=False, copy=False)
    is_confirmed = fields.Boolean(string='Confirmed', default=False, copy=False)
    is_cancelled = fields.Boolean(string='Cancelled', default=False, copy=False)

    @api.model
    def default_get(self, fields_list):
        vals = super(WholeSaleRequisition, self).default_get(fields_list)
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

    @api.onchange('login_employee_id', 'analytic_account_id')
    def onchange_login_employee(self):
        self._check_access()

    @api.depends('picking_ids')
    def get_picking_status(self):
        self.is_picking_done = False
        check_data = self.picking_ids.filtered(lambda l: l.state == 'done')
        if check_data:
            self.is_picking_done = True

    def _get_current_employee(self):
        if request.session.emp_id:
            return int(request.session.emp_id)
        elif not self.env.user.is_concurrent_user:
            return int(self.env.user.employee_id.id)
        else:
            return False

    login_employee_id = fields.Many2one(
        'hr.employee',
        string="Employee",
        default=lambda self: self._get_current_employee()
    )

    @api.depends('is_whole_sale', 'is_retail_sale')
    def get_sale_type(self):
        for rec in self:
            if rec.is_whole_sale:
                rec.sale_type = 'whole_sale'
            elif rec.is_retail_sale:
                rec.sale_type = 'retail_sale'
            else:
                rec.sale_type = False

    @api.depends('picking_ids')
    def _compute_received_picking_ids(self):
        for order in self:
            picking_id = self.env['stock.picking'].search(
                [('sale_requisition_id', '=', order.id), ('is_good_received', '=', True)])
            order.good_received_count = len(picking_id)

    @api.depends('picking_ids')
    def _compute_issued_picking_ids(self):
        for order in self:
            picking_id = self.env['stock.picking'].search(
                [('sale_requisition_id', '=', order.id), ('is_good_issued', '=', True)])
            order.good_issued_count = len(picking_id)

    def action_view_receipt(self):
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        pickings = self.mapped('picking_ids')
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids), ('is_good_received', '=', True)]
        elif pickings:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        return action

    def action_view_issued(self):
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        pickings = self.mapped('picking_ids')
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids), ('is_good_issued', '=', True)]
        elif pickings:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        return action

    def unlink(self):
        if not 'draft' in self.mapped('state'):
            raise UserError(_('You cannot delete a Requisition which is Approved.'))
        return super(WholeSaleRequisition, self).unlink()

    @api.model
    def create(self, vals):

        short_code = self.env['res.company'].browse(vals['company_id']).short_code
        if not short_code:
            raise ValidationError('Please Insert Company Short Code')
        else:
            vals['reference_no'] = str(short_code) + '/' + self.env['ir.sequence'].next_by_code(
                'whole.sale.requisition') or _(
                'New')
        res = super(WholeSaleRequisition, self).create(vals)
        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])
            res.write({
                'req_by_sign': employee_id.user_signature,
                'req_by_name': employee_id.id,
            })

        else:
            res.write({
                'req_by_sign': self.env.user.employee_id.user_signature,
                'req_by_name': self.env.user.employee_id.id,
            })

        res.write({'state': 'draft'})
        return res

    @api.constrains('sale_type')
    def check_whole_sale(self):
        for rec in self:
            if rec.sale_type == False:
                raise UserError('Please Select a Whole Sale or Retail Sale')

    def _prepare_picking_values(self, picking_type):

        transit_location = self.env['stock.location'].search(
            [('company_id', '=', self.env.company.id), ('usage', '=', 'transit')], limit=1)
        if not transit_location:
            raise UserError('Transit location of current company is missing.')

        """SEARCH ROOT WAREHOUSE PICKING TYPE """
        date_time = datetime.min.time()
        date = datetime.combine(self.scheduled_date, date_time)
        date_time_str = date.strftime("%Y-%m-%d %H:%M:%S")
        if picking_type == 'receipt':
            picking_type_id = False
            warehouses = self.env['stock.warehouse'].search([])

            for warehouse in warehouses:
                root_location_id = warehouse.lot_stock_id.id
                location_ids = self.env['stock.location'].search([('id', 'child_of', root_location_id)]).ids
                if self.from_location_id.id in location_ids:
                    picking_type_id = warehouse.in_type_id.id
            values = {

                'location_id': transit_location.id,
                'location_dest_id': self.from_location_id.id,
                'picking_type_id': picking_type_id,
                'scheduled_date': (self.scheduled_date + relativedelta(hours=6, minutes=30)).strftime(
                    '%d/%m/%Y %H:%M:%S'),
                'is_good_received': self.is_good_received,
                'analytic_account_id': self.analytic_account_id.id,
                'date': date_time_str,
            }
        else:
            picking_type_id = False
            warehouses = self.env['stock.warehouse'].search([])

            for warehouse in warehouses:
                root_location_id = warehouse.lot_stock_id.id
                location_ids = self.env['stock.location'].search([('id', 'child_of', root_location_id)]).ids
                if self.to_location_id.id in location_ids:
                    picking_type_id = warehouse.out_type_id.id

            if not picking_type_id:
                raise UserError(_(" Parent Location is Missing for  - %s ! ") % self.to_location_id.name)
            values = {
                'location_dest_id': transit_location.id,
                'location_id': self.to_location_id.id,
                'picking_type_id': picking_type_id,
                'scheduled_date': (self.scheduled_date + relativedelta(hours=6, minutes=30)).strftime(
                    '%d/%m/%Y %H:%M:%S'),
                'is_good_issued': self.is_good_issued,
                'analytic_account_id': self.analytic_account_id.id,
                'date': date_time_str,

            }
        values.update({
            'origin': self.reference_no,
            'company_id': self.mapped('company_id').id,
            'user_id': self.env.user.id,
            'sale_requisition_id': self.id,
            'is_already_sale_requisition': True,
        })
        return values

    @api.onchange('is_retail_sale', 'analytic_account_id')
    def onchange_retail_sale(self):
        if self.is_retail_sale and self.analytic_account_id:
            location_ids = self.env['account.analytic.account'].search(
                [('id', '=', self.analytic_account_id.id)]).location_id
            self.from_location_id = location_ids.id
            return {'domain': {'from_location_id': [('id', '=', location_ids.id)]}}
        else:
            return {'domain': {'from_location_id': []}}

    def action_confirm(self):
        for rec in self.requisition_line_ids:
            if rec.required_qty <= 0:
                raise ValidationError(
                    _("Please insert Required Quantity of  Product Name  ( %s)" % (rec.product_id.name)))
        if not self.user_id:
            raise UserError('Please Choose an approval person!!')

        picking_data = self.env['stock.picking'].search([('sale_requisition_id', '=', self.id)])
        if picking_data:
            self.approved_by_sign = False
            self.approved_by_name = False
        else:
            if request.session.emp_id:
                data = int(request.session.emp_id)
                employee_id = self.env['hr.employee'].search([('id', '=', data)])

                self.confirm_by_sign = employee_id.user_signature
                self.confirm_by_name = employee_id.id
            else:
                self.confirm_by_sign = self.env.user.employee_id.user_signature
                self.confirm_by_name = self.env.user.employee_id.id
        self.write({'state': 'confirm'})

    def approve_action(self):
        stock_moves = []
        lines = self.requisition_line_ids.filtered(lambda line: not line.display_type)
        if not lines:
            raise UserError('Please add at least one product line!')
        issue_picking = self.env['stock.picking'].create(self._prepare_picking_values('issue'))
        receipt_picking = self.env['stock.picking'].create(self._prepare_picking_values('receipt'))

        for line in lines:
            stock_moves.append(line._prepare_move_values(issue_picking, 'issued'))
            stock_moves.append(line._prepare_move_values(receipt_picking, 'received'))
        self.env['stock.move'].create(stock_moves)
        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])
            self.approved_by_sign = employee_id.user_signature
            self.approved_by_name = employee_id.id
        else:
            self.approved_by_sign = self.env.user.employee_id.user_signature
            self.approved_by_name = self.env.user.employee_id.id
        self.write({'state': 'approved'})

    def action_approved(self):
        for rec in self.requisition_line_ids:
            if rec.allowed_qty <= 0:
                raise ValidationError(_("Please Set Allowed Quantity of  Product Name  ( %s)" % (rec.product_id.name)))
        if not self.is_first_picking:
            self.approve_action()
            self.is_first_picking = True
        else:
            check_picking_status = self.env['stock.picking'].search(
                [('sale_requisition_id', '=', self.id)])
            if check_picking_status:
                is_already_requisition = check_picking_status.filtered(lambda b: b.is_already_sale_requisition == True)
                if not is_already_requisition:
                    self.approve_action()

    def action_cancel(self):
        self.is_confirmed = False
        picking_ids = self.env['stock.picking'].search([('sale_requisition_id', '=', self.id)])
        check_picking = False
        if picking_ids:
            check_picking = picking_ids.filtered(lambda a: a.state == 'done')
        if check_picking:
            raise ValidationError(
                "You Can't Cancel.Because Picking state is already Done.Please Refresh Your Browser Thanks")
        else:
            for picking in picking_ids:
                picking.write(
                    {'state': 'cancel', 'is_already_sale_requisition': False})

            self.write({'state': 'cancel'})


class WholeSaleRequisitionLine(models.Model):
    _name = 'whole.sale.requisition.line'
    _description = 'Whole Sale Requisition Line'

    product_id = fields.Many2one('product.product', string='Product')

    requisition_id = fields.Many2one('whole.sale.requisition', string='Requisition', ondelete='cascade', index=True,
                                     copy=False)
    sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of sale quote lines.",
                              default=10)
    name = fields.Text('Description ', translate=True)
    state = fields.Selection(
        related='requisition_id.state', string='Requisition Status', copy=False, store=True)
    remark = fields.Text(string='Remark')
    on_hand_qty = fields.Float(default=0.0, string='Stock Balance', compute='_get_onhand_qty')
    product_uom_id = fields.Many2one('uom.uom', 'UOM', related='product_id.uom_id', required=False, store=True)
    required_qty = fields.Float(string='Required Qty', default=0.0)
    allowed_qty = fields.Float(string='Allowed Qty', default=0.0)
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    packaging_size = fields.Float(string='Packaging Size', default=0.0)
    product_packaging_id = fields.Many2one('product.packaging', string='Packaging', default=False,
                                           domain="[('sales', '=', True), ('product_id','=',product_id)]",
                                           check_company=True)
    scheduled_date = fields.Datetime(string='Expected Date', related='requisition_id.scheduled_date')
    scheduled_datetime = fields.Datetime(string='Expected Datetime', default=fields.Datetime.now())

    issued_qty = fields.Float(
        'Issue Qty', default=0.0,
        digits='Product Unit of Measure')
    received_qty = fields.Float(
        'Received Qty', default=0.0,
        digits='Product Unit of Measure')

    def write(self, values):
        first_qty = self.required_qty
        change_qty = values.get('required_qty')
        first_muom_id = self.multi_uom_line_id.id
        change_muom_id = values.get('multi_uom_line_id')
        res = super(WholeSaleRequisitionLine, self).write(values)
        if change_muom_id:
            if change_muom_id and change_muom_id != first_muom_id:
                first_uom = self.env['multi.uom.line'].browse(first_muom_id).uom_id.name
                change_uom = self.env['multi.uom.line'].browse(change_muom_id).uom_id.name
                message = (f"MUOM: {first_uom} ==> {change_uom}.")
                self.requisition_id.message_post(body=message)
        if change_qty:
            if change_qty > 0 and first_qty != change_qty:
                message = (f"REQUEST QTY: {first_qty} ==> {change_qty}.0")
                self.requisition_id.message_post(body=message)
        if 'display_type' in values and self.filtered(lambda line: line.display_type != values.get('display_type')):
            raise UserError(
                _("You cannot change the type of a sale quote line. Instead you should delete the current line and create a new line of the proper type."))
        return res

    def _get_onhand_qty(self):
        for rec in self:
            if rec.requisition_id.from_location_id:
                mwh_id = rec.requisition_id.from_location_id.warehouse_id.id
                rec.name = rec.product_id.get_product_multiline_description_sale()
                rec.on_hand_qty = 0.00
                if rec.product_id:
                    main_warehouse_id = self.env['stock.warehouse'].search([('id', '=', mwh_id)], limit=1)
                    mwh_onhand_qty = sum(
                        self.env['stock.quant']._gather(rec.product_id, main_warehouse_id.lot_stock_id).mapped(
                            'quantity'))
                    rec.on_hand_qty = mwh_onhand_qty
            else:
                rec.on_hand_qty = 0.00

    def _prepare_move_values(self, picking, requestion_type):
        self.ensure_one()
        vals = {
            'origin': self.requisition_id.reference_no,
            'company_id': self.requisition_id.company_id.id,
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_id.id,
            'description_picking': self.name,
            'name': self.name,
            'state': 'draft',
            'multi_uom_qty': self.allowed_qty,
            # 'product_uom_qty':self.allowed_qty,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
            'picking_id': picking.id,
            'packaging_size':self.packaging_size,
            'product_packaging_id': self.product_packaging_id.id,
            'picking_type_id': picking.picking_type_id.id,
            'ws_req_line_id': self.id,
            'requestion_type': requestion_type,
            'remark': self.remark,
        }
        return vals

    @api.onchange('product_id')
    def onchange_product(self):
        for rec in self:
            rec.name = rec.product_id.name

    @api.onchange('product_packaging_id', 'product_uom_id', 'allowed_qty')
    def _onchange_update_product_packaging_qty(self):
        if not self.product_packaging_id:
            self.packaging_size = False
        else:
            packaging_uom = self.product_packaging_id.product_uom_id
            packaging_uom_qty = self.product_uom_id._compute_quantity(self.allowed_qty, packaging_uom)
            self.packaging_size = float_round(packaging_uom_qty / self.product_packaging_id.qty,
                                              precision_rounding=packaging_uom.rounding)
