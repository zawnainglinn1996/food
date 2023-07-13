import datetime
import json
from odoo import models, fields, api, _
from datetime import timedelta

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def get_stock_picking_issued(self):
        index = 1
        records = []

        for order in self:

            total_demand_qty = 0
            total_issued_qty = 0
            move_ids = order.move_ids_without_package
            if move_ids:
                for move_id in move_ids:
                    total_demand_qty += move_id.product_uom_qty
                    total_issued_qty += move_id.quantity_done

            move_ids_without_package = []
            for move in order.move_ids_without_package:
                date_deadline = ''
                if move.date_deadline:
                    date_deadline = (move.date_deadline + timedelta(hours=6, minutes=30)).strftime("%d/%m/%Y")
                move_ids_without_package.append({
                    'sr': index,
                    'product': move.product_id.name or '',
                    'brand': move.product_id.brand_id.name or '',
                    'description': move.product_id.name or '',
                    'uom': move.product_id.uom_id.name or '',
                    'demand_qty': move.product_uom_qty or '0',
                    'issued_qty': move.quantity_done or '0',
                    'lot_ser_no': move.lot_ids.name or '',
                    'expired_date': move.lot_ids.expiration_date.date() if move.lot_ids.expiration_date else '',
                    'remark': move.remark or '',
                })
                index += 1

            records.append({
                    'gin': order.name or '',
                    'dep_to': order.login_employee_id.department_id.complete_name or '',
                    'scheduled_date': (order.scheduled_date + timedelta(hours=6, minutes=30)).strftime("%d/%m/%Y") if order.scheduled_date else '',
                    'dep_from': order.location_id.complete_name or '',
                    'source_doc': order.origin or '',
                    'analytic_account_name': order.analytic_account_id.name or '',
                    'issued_by_sign': order.issued_by_sign or '',
                    'issued_by_name': order.issued_by_id.name or '',
                    'received_by_sign': order.received_by_sign or '',
                    'received_by_name': order.received_by_id.name or '',
                    'total_demand_qty': total_demand_qty or '0',
                    'total_issued_qty': total_issued_qty or '0',
                    'move_ids_without_package': move_ids_without_package,
                })
        return self.env.ref('report_form.action_stock_picking_issued_pdf_report').report_action(self, data={'records': records})

    def get_stock_picking_received(self):
        index = 1
        records = []

        for order in self:

            total_received_qty = 0
            total_demand_qty = 0
            move_ids = order.move_ids_without_package
            if move_ids:
                for move_id in move_ids:
                    total_demand_qty += move_id.product_uom_qty
                    total_received_qty += move_id.quantity_done

            move_ids_without_package = []
            for move in order.move_ids_without_package:

                date_deadline = ''
                if move.date_deadline:
                    date_deadline = (move.date_deadline + timedelta(hours=6, minutes=30)).strftime("%d/%m/%Y")

                move_ids_without_package.append({
                    'sr': index,
                    'product': move.product_id.name or '',
                    'brand': move.product_id.brand_id.name or '',
                    'description': move.product_id.name or '',
                    'uom': move.product_id.uom_id.name or '',
                    'demand_qty': move.product_uom_qty or '0',
                    'received_qty': move.quantity_done or '0',
                    'lot_ser_no': move.lot_ids.name or '',
                    'expired_date': date_deadline or '',
                    'remark': move.remark or '',
                })
                index += 1

            records.append({
                'grn': order.name or '',
                'dep_to': order.location_dest_id.complete_name or '',
                'scheduled_date': (order.scheduled_date + timedelta(hours=6, minutes=30)).strftime("%d/%m/%Y") or '',
                'analytic_account_name': order.analytic_account_id.name or '',
                'dep_from': order.location_id.complete_name or '',
                'source_doc': order.origin or '',
                'issued_by_sign': order.issued_by_sign or '',
                'issued_by_name': order.issued_by_id.name or '',
                'received_by_sign': order.received_by_sign or '',
                'received_by_name': order.received_by_id.name or '',
                'total_demand_qty': total_demand_qty or 0,
                'total_received_qty': total_received_qty or 0,
                'move_ids_without_package': move_ids_without_package,
                })
        return self.env.ref('report_form.action_stock_picking_received_pdf_report').report_action(self, data={'records': records})
