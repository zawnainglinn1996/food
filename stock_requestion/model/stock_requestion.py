import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict
from odoo.http import request


class StockRequestion(models.Model):
    _name = 'stock.requestion'
    _description = 'Stock Requestion'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'document_no'
    _order = 'created_date desc, id desc'

    document_no = fields.Char(string='Document')
    created_date = fields.Datetime(string='Created Date', default=fields.Datetime.now, readonly=True,copy=False)
    product_family_id = fields.Many2one('product.family', string='Product Family')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company,
                                 required=True, )
    scheduled_date = fields.Datetime(string='Scheduled Date')
    state = fields.Selection(
        [('draft', 'Draft'),
         ('submit', 'Submit'),
         ('verified', 'Verified'),
         ('approved', 'Approved'),
         ('confirm', 'Confirmed'),
         ('cancel', 'Canceled')], string='State', readonly=True, index=True, copy=False, default='draft', tracking=1)
    stock_requestion_line = fields.One2many('stock.requestion.line', 'requestion_id', string='Stock Requestion Line',
                                            states={'cancel': [('readonly', True)],
                                                    'submit': [('readonly', True)],
                                                    'approved': [('readonly', True)],
                                                    'verified': [('readonly', True)],
                                                    'confirm': [('readonly', True)]},
                                            copy=True)
    user_id = fields.Many2one('res.users', string='To Approve')
    product_id = fields.Many2one('product.product', related='stock_requestion_line.product_id', string='Product')
    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Operation Type',
        required=False)
    req_by_sign = fields.Binary(string='Request Sign', help='For Req By Sign')
    req_by_name = fields.Many2one('hr.employee', string='Reuest Name', help='For Req By Name')
    req_by_position = fields.Char(string='Request Position', help='For Req By Position')

    approved_by_sign = fields.Binary(string='Approved Sign', help='for approved by sign')
    approved_by_name = fields.Many2one('hr.employee', string='Approved Name', help='For Approved by name')
    approved_by_position = fields.Char(string='Approved Position', help='For Approved By Position')

    verified_by_sign = fields.Binary(string='Verified Sign', help='For Verified By Sign')
    verified_by_name = fields.Many2one('hr.employee', string='Verified Name ', help='Verified BY Name')
    verified_by_position = fields.Char(string='Verified Position', help='For Verified By Position')

    confirm_by_sign = fields.Binary(string='Confirmed Sign', help='For Confirm By Sign')
    confirm_by_name = fields.Many2one('hr.employee', string='Confirmed Name ', help='Confirm BY Name')
    confirm_by_position = fields.Char(string='Confirmed Position', help='For Confirm By Position')

    picking_ids = fields.One2many('stock.picking', 'requestion_id', string='Pickings')
    good_received_count = fields.Integer(string='Received ', compute='_compute_received_picking_ids', store=True)
    good_issued_count = fields.Integer(string='Issued', compute='_compute_issued_picking_ids', store=True)

    is_good_issued = fields.Boolean(string='Issued?', default='True')
    is_good_received = fields.Boolean(string='Received', default='True')

    request_from = fields.Many2one('stock.location', string='Request From')
    request_to = fields.Many2one('stock.location', string='Request To', default='True',
                                 domain="[('usage', '=', 'internal')]")

    is_picking_done = fields.Boolean(string='Is Picking Done', compute='get_picking_status', copy=False)
    is_first_picking = fields.Boolean(string='First Picking', default=False, copy=False)
    is_submit = fields.Boolean(string='Submitted', default=False, copy=False)
    is_verified = fields.Boolean(string='Verified', default=False, copy=False)
    is_approved = fields.Boolean(string='Approved', default=False, copy=False)
    is_cancelled = fields.Boolean(string='Cancelled', default=False, copy=False)

    is_access_submit = fields.Boolean('Access Submit', compute='_check_access')
    is_access_verified = fields.Boolean('Access Verified', compute='_check_access')
    is_access_approve = fields.Boolean('Access Approve', compute='_check_access')
    is_access_confirm = fields.Boolean('Access Confirm', compute='_check_access')
    is_access_cancel = fields.Boolean('Access Cancel', compute='_check_access')

    def _check_access(self):
        self.is_access_submit = self.is_access_verified = self.is_access_approve= self.is_access_confirm = self.is_access_cancel = False
        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])
            if employee_id:
                if employee_id.is_submit_stock_req:
                    self.is_access_submit = True
                if employee_id.is_verified_stock_req:
                    self.is_access_verified = True
                if employee_id.is_approved_stock_req:
                    self.is_access_approve = True
                if employee_id.is_confirm_stock_req:
                    self.is_access_confirm = True
                if employee_id.is_cancel_stock_req:
                    self.is_access_cancel = True

    @api.depends('picking_ids')
    def get_picking_status(self):
        self.is_picking_done = False
        check_data = self.picking_ids.filtered(lambda l: l.state == 'done')
        if check_data:
            self.is_picking_done = True

    @api.onchange('login_employee_id')
    def onchange_login_employee(self):
        self._check_access()
        self.request_from = self.login_employee_id.location_id
        main_location_id = self.env['stock.warehouse'].search([('is_main_wh', '=', True)]).lot_stock_id
        for main_loc_id in main_location_id:
            self.request_to = main_loc_id.id

    def unlink(self):
        if not 'draft' in self.mapped('state'):
            raise UserError(_('You cannot delete a Requisition which is Approved.'))
        return super(StockRequestion, self).unlink()

    @api.model
    def create(self, vals):
        res = super(StockRequestion, self).create(vals)
        short_code = self.env['res.company'].browse(vals['company_id']).short_code
        if not short_code:
            raise ValidationError('Please Insert Company Short Code')
        else:
            res.document_no = str(short_code) + '/' + self.env['ir.sequence'].next_by_code('stock.requestion') or _(
                'New')
        return res

    def action_cancel(self):
        if self.is_cancelled:
            raise ValidationError(
                _("This Record is already ( %s) . Please Refresh Your Browser Thanks!!!!" % (self.state)))
        else:
            self.is_submit = False
            self.is_approved = False
            self.is_verified = False
            picking_ids = self.env['stock.picking'].search([('requestion_id', '=', self.id)])
            check_picking = False
            if picking_ids:
                check_picking = picking_ids.filtered(lambda a: a.state == 'done')
            if check_picking:
                raise ValidationError(
                    "You Can't Cancel.Because Picking state is already Done.Please Refresh Your Browser Thanks")
            else:
                for picking in picking_ids:
                    picking.write(
                        {'state': 'cancel', 'is_already_requisition': False})

                self.write({'state': 'cancel'})
                self.is_cancelled = True

    def action_draft(self):
        self.write({'state': 'draft'})
        return {}

    def action_submit(self):
        if self.is_submit:
            raise ValidationError(
                _("This Record is already ( %s) . Please Refresh Your Browser Thanks!!!!" % (self.state)))
        lines = self.stock_requestion_line.filtered(lambda line: not line.display_type)
        if not lines:
            raise UserError('!!!Please add at least one product line!!!')
        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])
            self.req_by_sign = employee_id.user_signature
            self.req_by_name = employee_id.id
            self.req_by_position = employee_id.job_title
        else:
            self.req_by_sign = self.env.user.employee_id.user_signature
            self.req_by_name = self.env.user.employee_id.id
            self.req_by_position = self.env.user.employee_id.job_title
        self.write({'state': 'submit'})
        self.is_submit = True

    def action_verified(self):
        if self.is_verified:
            raise ValidationError(
                _("This Record is already ( %s) . Please Refresh Your Browser Thanks!!!!" % (self.state)))
        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])
            self.verified_by_sign = employee_id.user_signature
            self.verified_by_name = employee_id.id
            self.verified_by_position = employee_id.job_title
        else:
            self.verified_by_sign = self.env.user.employee_id.user_signature
            self.verified_by_name = self.env.user.employee_id.id
            self.verified_by_position = self.env.user.employee_id.job_title
        self.write({'state': 'verified'})
        self.is_verified = True

    def action_approved(self):
        if self.is_approved:
            raise ValidationError(
                _("This Record is already ( %s) . Please Refresh Your Browser Thanks!!!!" % (self.state)))
        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])
            self.approved_by_sign = employee_id.user_signature
            self.approved_by_name = employee_id.id
            self.approved_by_position = employee_id.job_title
        else:
            self.approved_by_sign = self.env.user.employee_id.user_signature
            self.approved_by_name = self.env.user.employee_id.id
            self.approved_by_position = self.env.user.employee_id.job_title
        self.write({'state': 'approved'})
        self.is_approved = True

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

    @api.depends('picking_ids')
    def _compute_received_picking_ids(self):
        for order in self:
            picking_id = self.env['stock.picking'].search(
                [('requestion_id', '=', order.id), ('is_good_received', '=', True)])
            order.good_received_count = len(picking_id)

    @api.depends('picking_ids')
    def _compute_issued_picking_ids(self):
        for order in self:
            picking_id = self.env['stock.picking'].search(
                [('requestion_id', '=', order.id), ('is_good_issued', '=', True)])
            order.good_issued_count = len(picking_id)

    def _prepare_picking_values(self, picking_type):
        transit_location = self.env['stock.location'].search(
            [('company_id', '=', self.env.company.id), ('usage', '=', 'transit')], limit=1)
        if not transit_location:
            raise UserError('Transit location of current company is missing.')

        """SEARCH ROOT WAREHOUSE PICKING TYPE """
        if picking_type == 'receipt':
            picking_type_id = False
            warehouses = self.env['stock.warehouse'].search([])
            for warehouse in warehouses:
                root_location_id = warehouse.lot_stock_id.id
                location_ids = self.env['stock.location'].search([('id', 'child_of', root_location_id)]).ids
                if self.request_from.id in location_ids:
                    picking_type_id = warehouse.in_type_id.id
            values = {

                'location_id': transit_location.id,
                'location_dest_id': self.request_from.id,
                'picking_type_id': picking_type_id,
                'is_good_received': self.is_good_received,
            }
        else:
            picking_type_id = False
            warehouses = self.env['stock.warehouse'].search([])
            for warehouse in warehouses:
                root_location_id = warehouse.lot_stock_id.id
                location_ids = self.env['stock.location'].search([('id', 'child_of', root_location_id)]).ids
                if self.request_to.id in location_ids:
                    picking_type_id = warehouse.out_type_id.id
            values = {
                'location_dest_id': transit_location.id,
                'location_id': self.request_to.id,
                'picking_type_id': picking_type_id,
                'is_good_issued': self.is_good_issued,
            }
        values.update({
            'origin': self.document_no,
            'company_id': self.mapped('company_id').id,
            'user_id': self.env.user.id,
            'requestion_id': self.id,
            'scheduled_date':self.scheduled_date,
            'is_already_requisition': True,
            'login_employee_id': self.login_employee_id.id,

        })
        return values

    def confirm_action(self):
        stock_moves = []
        lines = self.stock_requestion_line.filtered(lambda line: not line.display_type)
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
            self.confirm_by_sign = employee_id.user_signature
            self.confirm_by_name = employee_id.id
            self.confirm_by_position = employee_id.job_title
        else:
            self.confirm_by_sign = self.env.user.employee_id.user_signature
            self.confirm_by_name = self.env.user.employee_id.id
            self.confirm_by_position = self.env.user.employee_id.job_title

        self.write({'state': 'confirm'})

    def action_confirm(self):
        if not self.is_first_picking:
            self.confirm_action()
            self.is_first_picking = True
        else:
            check_picking = self.env['stock.picking'].search(
                [('requestion_id', '=', self.id)])
            if check_picking:
                is_already_requisition = check_picking.filtered(lambda b: b.is_already_requisition == True)
                # IF NOT PICKING
                if not is_already_requisition:
                    self.confirm_action()


class StockRequestionLine(models.Model):
    _name = 'stock.requestion.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Stock Requestion Line'

    sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of sale quote lines.",
                              default=10)
    name = fields.Text('Description ', translate=True)
    requestion_id = fields.Many2one('stock.requestion', string='Reference', required=True, ondelete='cascade',
                                    index=True,
                                    copy=False)
    product_id = fields.Many2one('product.product', 'Product',
                                 domain="[('product_family_id','=',parent.product_family_id)]")
    brand_id = fields.Many2one('product.brand', related='product_id.brand_id', string='Brand')
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")

    product_uom = fields.Many2one('uom.uom', 'UOM', related='product_id.uom_id', required=False)
    product_uom_qty = fields.Float(
        'Request Qty', default=1.0,
        digits='Product Unit of Measure', required=True, tracking=2)
    issued_qty = fields.Float(
        'Issue Qty', default=0.0,
        digits='Product Unit of Measure')
    received_qty = fields.Float(
        'Received Qty', default=0.0,
        digits='Product Unit of Measure')
    scheduled_date = fields.Datetime(string='Scheduled_date')
    reason = fields.Char(string='Reason')
    remark = fields.Text(string='Remark')

    forecasted_issue = fields.Boolean(compute='_compute_forecasted')
    move_ids = fields.One2many('stock.move', 'stock_req_id', string='Stock Moves')

    state = fields.Selection(
        related='requestion_id.state', string='Requestion Status', copy=False, store=True)

    onhand_at_date = fields.Float(compute='_compute_qty_at_date')
    on_hand_qty = fields.Float('Stock Balance', default=0.0, digits='Product Stock Balance')

    @api.depends('product_id',
                 'product_uom_qty',
                 'product_uom',
                 'requestion_id.scheduled_date')
    def _compute_qty_at_date(self):
        for rec in self:
            product = rec.product_id
            if product:
                out_moves = self.env['stock.move'].sudo().search([('product_id', '=', product.id),
                                                                  ('location_id.usage', '=', 'internal'),
                                                                  ('state', '=', 'done')])
                in_moves = self.env['stock.move'].sudo().search([('product_id', '=', product.id),
                                                                 ('location_dest_id.usage', '=', 'internal'),
                                                                 ('state', '=', 'done')])
                qty = sum(in_moves.mapped('product_qty')) - sum(out_moves.mapped('product_qty'))
            else:
                qty = 0
            rec.onhand_at_date = qty

    @api.depends('product_uom_qty', 'scheduled_date')
    def _compute_forecasted(self):
        for line in self:
            warehouse = line.requestion_id.picking_type_id.warehouse_id
            line.forecasted_issue = False
            if line.product_id:
                virtual_available = line.product_id.with_context(warehouse=warehouse.id,
                                                                 to_date=line.scheduled_date).virtual_available
                if line.requestion_id.state == 'draft':
                    virtual_available += line.product_uom_qty
                if virtual_available < 0:
                    line.forecasted_issue = True

    @api.onchange('product_id')
    def onchange_product(self):
        for rec in self:
            rec.scheduled_date = rec.requestion_id.scheduled_date
            rec.name = rec.product_id.get_product_multiline_description_sale()
            rec.on_hand_qty = 0.00
            if rec.product_id:
                domain = [('lot_stock_id', '=', rec.requestion_id.request_from.id)]
                main_warehouse_id = self.env['stock.warehouse'].search(domain)
                # main_warehouse_id = self.env['stock.warehouse'].search([('is_main_wh', '=', True)], limit=1)
                mwh_onhand_qty = sum(
                    self.env['stock.quant']._gather(rec.product_id, main_warehouse_id.lot_stock_id).mapped(
                        'quantity'))
                rec.on_hand_qty = mwh_onhand_qty

    @api.model
    def create(self, values):
        if values.get('display_type', self.default_get(['display_type'])['display_type']):
            values.update(product_id=False, product_uom_qty=0, product_uom=False)
        return super(StockRequestionLine, self).create(values)

    def write(self, values):
        first_qty = self.product_multi_uom_qty
        change_qty = values.get('product_multi_uom_qty')
        first_muom_id = self.multi_uom_line_id.id
        change_muom_id = values.get('multi_uom_line_id')
        res = super(StockRequestionLine, self).write(values)
        if change_muom_id:
            if change_muom_id and change_muom_id != first_muom_id:
                first_uom = self.env['multi.uom.line'].browse(first_muom_id).uom_id.name
                change_uom = self.env['multi.uom.line'].browse(change_muom_id).uom_id.name
                message = (f"MUOM: {first_uom} ==> {change_uom}.")
                self.requestion_id.message_post(body=message)
        if change_qty:
            if change_qty > 0 and first_qty != change_qty:
                message = (f"REQUEST QTY: {first_qty} ==> {change_qty}.0")
                self.requestion_id.message_post(body=message)
        if 'display_type' in values and self.filtered(lambda line: line.display_type != values.get('display_type')):
            raise UserError(
                _("You cannot change the type of a sale quote line. Instead you should delete the current line and create a new line of the proper type."))
        return res

    def _prepare_move_values(self, picking, requestion_type):
        self.ensure_one()
        return {
            'origin': self.requestion_id.document_no,
            'company_id': self.requestion_id.company_id.id,
            'product_id': self.product_id.id,
            'product_uom': self.product_uom.id,
            'description_picking': self.name,
            'name': self.name,
            'state': 'draft',
            'product_uom_qty': self.product_uom_qty,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
            'picking_id': picking.id,
            'picking_type_id': picking.picking_type_id.id,
            'brand_id': self.brand_id.id,
            'stock_req_id': self.id,
            'requestion_type': requestion_type,
            'remark': self.remark,
        }

    def action_product_forecast_report(self):
        self.ensure_one()
        action = self.product_id.action_product_forecast_report()
        action['context'] = {
            'active_id': self.product_id.id,
            'active_model': 'product.product',
            'purchase_line_to_match_id': self.id,
        }
        warehouse = self.requestion_id.picking_type_id.warehouse_id
        if warehouse:
            action['context']['warehouse'] = warehouse.id
        return action

    _sql_constraints = [
        ('accountable_product_id_required',
         "CHECK(display_type IS NOT NULL OR (product_id IS NOT NULL))",
         "Missing required product and UoM on accountable purchase quote line."),

        ('non_accountable_fields_null',
         "CHECK(display_type IS NULL OR (product_id IS NULL))",
         "Forbidden product, unit price, quantity, and UoM on non-accountable purchase quote line"),
    ]
