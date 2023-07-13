from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.http import request


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    requestion_id = fields.Many2one('stock.requestion', string='Requestion',copy=False)
    is_good_issued = fields.Boolean(string='Issued?', default=False)
    is_good_received = fields.Boolean(string='Received', default=False)
    company_id = fields.Many2one(copy=True)
    issued_by_sign = fields.Binary(string='Issued By Sign', help='Issued By Sign', copy=False)
    issued_by_id = fields.Many2one('hr.employee', string='Name')

    received_by_sign = fields.Binary(string='Received by Sign', copy=False)
    received_by_id = fields.Many2one('hr.employee', string='Received Name', copy=False)
    is_already_requisition = fields.Boolean(string='Already Requested')

    def action_cancel(self):
        res = super(StockPicking, self).action_cancel()
        self.is_already_requisition = False
        return res

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        if self.is_good_issued:
                if request.session.emp_id:
                    data = int(request.session.emp_id)
                    employee_id = self.env['hr.employee'].search([('id', '=', data)])
                    self.write({
                        'issued_by_sign': employee_id.user_signature,
                        'issued_by_id': employee_id.id
                    })
                else:
                    self.write({
                        'issued_by_sign': self.env.user.employee_id.user_signature,
                        'issued_by_id': self.env.user.employee_id.id
                    })
        elif self.is_good_received:
            if request.session.emp_id:
                data = int(request.session.emp_id)
                employee_id = self.env['hr.employee'].search([('id', '=', data)])
                self.write({
                    'received_by_sign': employee_id.user_signature,
                    'received_by_id': employee_id.id
                })
            else:
                self.write({
                    'received_by_sign': self.env.user.employee_id.user_signature,
                    'received_by_id': self.env.user.employee_id.id
                })
        else:
            if request.session.emp_id:
                data = int(request.session.emp_id)
                employee_id = self.env['hr.employee'].search([('id', '=', data)])
                self.write({
                    'issued_by_sign': employee_id.user_signature,
                    'issued_by_id': employee_id.id
                })
            else:
                self.write({
                    'issued_by_sign': self.env.user.employee_id.user_signature,
                    'issued_by_id': self.env.user.employee_id.id
                })


        return res

    def get_warehouse(self, location_id):
        wh_code = self.env['stock.warehouse']
        warehouses = self.env['stock.warehouse'].search([])
        for warehouse in warehouses:
            root_location_id = warehouse.lot_stock_id.id
            location_ids = self.env['stock.location'].search([('id', 'child_of', root_location_id)]).ids
            if location_id in location_ids:
                wh_code = warehouse
                break
        return wh_code

    @api.model
    def create(self, vals):
        defaults = self.default_get(['name', 'picking_type_id'])
        company_code = self.env.company.short_code
        if not company_code:
            raise UserError('PLEASE INSERT COMPANY SHORT CODE')
        requestion_id = self.env['stock.requestion'].browse(vals.get('requestion_id')).id
        sale_requisition_id = self.env['whole.sale.requisition'].browse(vals.get('sale_requisition_id')).id
        if requestion_id or sale_requisition_id:
            issued = vals.get('is_good_issued')
            received = vals.get('is_good_received')

            location_dest_id = self.env['stock.location'].browse(vals.get('location_dest_id'))
            location_id = self.env['stock.location'].browse(vals.get('location_id'))
            if issued:
                if location_id.usage == 'internal' and location_dest_id.usage == 'transit':
                    wh_code = self.get_warehouse(location_id.id)
                else:
                    wh_code = self.get_warehouse(location_dest_id.id)
                vals['name'] = str(company_code) + '/' + str(wh_code.code) + '/GIN-' + self.env[
                    'ir.sequence'].next_by_code('stock.picking.issued') or _('New')

            elif received:
                if location_id.usage == 'transit' and location_dest_id.usage == 'internal':
                    wh_code = self.get_warehouse(location_dest_id.id)
                else:
                    wh_code = self.get_warehouse(location_id.id)
                vals['name'] = str(company_code) + '/' + str(wh_code.code) + '/GRN-' + self.env[
                    'ir.sequence'].next_by_code('stock.picking.received') or _('New')
            else:
                pass
        else:
            picking_type = self.env['stock.picking.type'].browse(
                vals.get('picking_type_id', defaults.get('picking_type_id')))
            if vals.get('name', '/') == '/' and defaults.get('name', '/') == '/' and vals.get('picking_type_id',
                                                                                              defaults.get(
                                                                                                  'picking_type_id')):
                if picking_type.sequence_id:
                    vals['name'] = picking_type.sequence_id.next_by_id()

        scheduled_date = vals.pop('scheduled_date', False)
        res = super(StockPicking, self).create(vals)
        return res
