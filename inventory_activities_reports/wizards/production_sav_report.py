import pytz
import logging
from itertools import groupby
from odoo import api, models, fields, _
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)


class ProductionSAVReportXlsx(models.AbstractModel):
    _name = 'report.inventory_activities_reports.production_sav_xlsx'
    _description = 'Production SAV Report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objects):
        tz = pytz.timezone(self.env.context.get('tz'))
        start_date_raw = datetime.strptime(data['start_date'], DEFAULT_SERVER_DATE_FORMAT)
        end_date_raw = datetime.strptime(data['end_date'] + ' 23:59:59', DEFAULT_SERVER_DATETIME_FORMAT)
        start_date = tz.localize(start_date_raw).astimezone(pytz.utc)
        end_date = tz.localize(end_date_raw).astimezone(pytz.utc)
        product_ids = data['product_ids']
        records = []

        sheet = workbook.add_worksheet('Production SAV Report')

        title = workbook.add_format({
            'font_name': 'Arial', 'font_size': 12, 'valign': 'vcenter', 'align': 'center', 'bold': True,
        })
        header = workbook.add_format({
            'font_name': 'Arial', 'font_size': 11, 'valign': 'vcenter', 'align': 'center', 'bold': True, 'border': 1,
        })
        cell_left = workbook.add_format({
            'font_name': 'Arial', 'font_size': 11, 'valign': 'vcenter', 'align': 'left', 'border': 1,
        })
        cell_center = workbook.add_format({
            'font_name': 'Arial', 'font_size': 11, 'valign': 'vcenter', 'align': 'center', 'border': 1,
        })
        cell_right = workbook.add_format({
            'font_name': 'Arial', 'font_size': 11, 'valign': 'vcenter', 'align': 'right', 'border': 1,
        })

        sheet.set_row(0, 25)

        sheet.set_column('A:A', 15)
        sheet.set_column('B:B', 25)
        sheet.set_column('C:C', 55)
        sheet.set_column('D:D', 12)
        sheet.set_column('E:E', 20)
        sheet.set_column('F:F', 20)
        sheet.set_column('G:G', 20)
        sheet.set_column('H:H', 15)
        sheet.set_column('I:I', 20)
        sheet.set_column('J:J', 15)

        sheet.merge_range('A1:J1', 'Production Standard, Actual and Variance Report', title)
        sheet.merge_range('A2:J2', '')
        sheet.merge_range('A3:J3', '')
        sheet.write('A4', '')
        sheet.write('B4', 'From Date:', cell_center)
        sheet.write('C4', start_date_raw.strftime('%d.%m.%y'), cell_center)
        sheet.write('D4', '')
        sheet.write('E4', 'To Date:', cell_center)
        sheet.merge_range('F4:G4', end_date_raw.strftime('%d.%m.%y'), cell_center)
        sheet.merge_range('A5:J5', '')

        sheet.write('A6', 'Date', header)
        sheet.write('B6', 'Mo Sequence', header)
        sheet.write('C6', 'Item', header)
        sheet.write('D6', 'UOM', header)
        sheet.write('E6', 'Standard Usage Qty', header)
        sheet.write('F6', 'Standard Usage UOM', header)
        sheet.write('G6', 'Actual Qty', header)
        sheet.write('H6', 'Actual UOM', header)
        sheet.write('I6', 'Different Qty', header)
        sheet.write('J6', 'Different UOM', header)
        if product_ids:
            domain = [('date_planned_start', '>=', start_date), ('date_planned_start', '<=', end_date),
                      ('state', '=', 'done'), ('product_id', 'in', product_ids)]
        else:
            domain = [('date_planned_start', '>=', start_date), ('date_planned_start', '<=', end_date),
                      ('state', '=', 'done')]
        records = self.env['mrp.production'].search(domain)

        row_index = 7

        for record in records:
            sheet.write(f'A{row_index}', record.date_planned_start.strftime('%d.%m.%y'), cell_left)
            sheet.write(f'B{row_index}', record.name or '', cell_left)
            sheet.write(f'C{row_index}', record.product_id.name or '', cell_left)
            sheet.write(f'D{row_index}', record.product_id.uom_id.name or '', cell_center)
            sheet.write(f'E{row_index}', record.standard_quantity or 0.0, cell_center)
            sheet.write(f'F{row_index}', record.product_uom_id.name or '', cell_center)
            sheet.write(f'G{row_index}', record.qty_producing or 0.0, cell_center)
            sheet.write(f'H{row_index}', record.product_uom_id.name or '', cell_center)
            sheet.write(f'I{row_index}', record.difference_quantity or 0.0, cell_center)
            sheet.write(f'J{row_index}', record.product_uom_id.name or '', cell_center)
            row_index += 1

            for move in record.move_raw_ids:
                sheet.write(f'A{row_index}', record.date_planned_start.strftime('%d.%m.%y'), cell_left)
                sheet.write(f'B{row_index}', record.name or '', cell_left)
                sheet.write(f'C{row_index}', move.product_id.name or '', cell_left)
                sheet.write(f'D{row_index}', move.product_id.uom_id.name or '', cell_center)
                sheet.write(f'E{row_index}', move.standard_qty or 0.0, cell_center)
                sheet.write(f'F{row_index}', move.product_uom.name or '', cell_center)
                sheet.write(f'G{row_index}', move.quantity_done or 0.0, cell_center)
                sheet.write(f'H{row_index}', move.product_uom.name or '', cell_center)
                sheet.write(f'I{row_index}', move.difference_qty or 0.0, cell_center)
                sheet.write(f'J{row_index}', move.product_uom.name or '', cell_center)
                row_index += 1


class ProductionSAVReport(models.TransientModel):
    _name = 'production.sav.report'
    _description = 'Production SAV Report'
    _rec_name = 'start_date'

    start_date = fields.Date('Start Date', required=1,
                             default=lambda self: fields.Date.context_today(self) + relativedelta(day=1))
    end_date = fields.Date('End Date', required=1,
                           default=lambda self: fields.Date.context_today(self) + relativedelta(day=31))

    product_ids = fields.Many2many('product.product', string='Products', domain=[('detailed_type', '=', 'product')])

    def btn_print(self):
        return self.env.ref('inventory_activities_reports.action_production_sav_report_xlsx').report_action(
            self,
            data={
                'start_date': self.start_date,
                'end_date': self.end_date,
                'product_ids': self.product_ids.ids
            })
