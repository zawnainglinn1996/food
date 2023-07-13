from odoo import models, fields, api, _
import pytz
from datetime import datetime
from dateutil import relativedelta
from dateutil.relativedelta import relativedelta
from itertools import groupby


class SaleAnalysisExcelReport(models.AbstractModel):
    _name = 'report.sale_analysis_excel_report.sale_analysis_excel_report'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Sale Analysis Report'

    @api.model
    def _get_data(self, options):
        date_from = options.get('date_from')
        date_to = options.get('date_to')
        analytic_account_ids = options['analytic_account_id']

        domain = [('date_order', '>=', date_from), ('date_order', '<=', date_to), ('state', '=', 'sale'),
                  ('analytic_account_id', 'in', analytic_account_ids)]

        order_ids = self.env['sale.order'].search(domain)
        sale_line_ids = []
        for order in order_ids:
            for line in order.order_line:
                order_date = line.order_id.date_order.strftime('%Y-%m-%d')
                expected_date = line.order_id.commitment_date.strftime('%Y-%m-%d')
                sale_line_ids.append({
                    'order_id': line.order_id.id,
                    'product_code': line.product_id.default_code or '-',
                    'product_name': line.product_id.name or '',
                    'date': order_date or '',
                    'expected_date':expected_date or '',
                    'order_no': line.order_id.name or '',
                    'order_qty': line.multi_uom_qty or 0.00,
                    'sale_price': line.multi_price_unit or 0.00,
                    'subtotal': line.price_subtotal or 0.00,
                })
        return sale_line_ids

    def generate_xlsx_report(self, workbook, data, docs):
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        analytic_account_ids = data.get('analytic_account_id')

        analytic_account_name = []
        for analytic in analytic_account_ids:
            analytic_id = self.env['account.analytic.account'].browse(analytic)
            analytic_account_name.append(analytic_id.name)
        separator = ', '
        analytic_name = separator.join(analytic_account_name)
        y_offset = 0

        format0 = workbook.add_format({
            'bold': True, 'align': 'center', 'font_size': 15,
            'bg_color': '#B0C4DE', 'valign': 'vcenter', 'border': True,'num_format': '#,##0.00'
        })
        format7 = workbook.add_format({
            'bold': True, 'align': 'center', 'font_size': 13,
            'bg_color': '#B0C4DE', 'valign': 'vcenter', 'border': True,'num_format': '#,##0.00'
        })
        format8 = workbook.add_format({
            'bold': True, 'border': True, 'align': 'left', 'font_size': 13, 'valign': 'vcenter','num_format': '#,##0.00'
        })
        format1 = workbook.add_format({
            'bold': True, 'border': True, 'align': 'center', 'font_size': 13, 'valign': 'vcenter','num_format': '#,##0.00'
        })
        format2 = workbook.add_format({
            'border': True, 'align': 'center', 'valign': 'vcenter',
        })
        format3 = workbook.add_format({
            'bold': True, 'border': True, 'align': 'right', 'font_size': 12, 'valign': 'vcenter','num_format': '#,##0.00'
        })
        format4 = workbook.add_format({
            'align': 'center', 'border': True, 'valign': 'vcenter', 'font_size': 12,'num_format': '#,##0.00'
        })
        format5 = workbook.add_format({
            'align': 'right', 'border': True, 'bold': False, 'font_size': 12,'num_format': '#,##0.00',
            'valign': 'vcenter', })
        format6 = workbook.add_format({
            'align': 'LEFT', 'border': True, 'valign': 'vcenter','font_size': 13,'num_format': '#,##0.00',
        })
        format7 = workbook.add_format({
            'align': 'LEFT', 'border': True, 'valign': 'vcenter', 'font_size': 12,'num_format': '#,##0.00'
        })

        sheet = workbook.add_worksheet('Sale Analysis Report')
        sheet.set_row(0, 30)
        sheet.set_row(1, 25)
        sheet.set_row(2, 25)
        sheet.set_row(3, 25)
        sheet.set_row(4, 25)

        sheet.set_column('A:A', 7)
        sheet.set_column('B:B', 23)
        sheet.set_column('C:C', 26)
        sheet.set_column('D:D', 35)
        sheet.set_column('E:E', 50)
        sheet.set_column('F:F', 35)
        sheet.set_column('G:G', 15)
        sheet.set_column('H:H', 15)
        sheet.set_column('I:I', 15)
        sheet.set_column('J:K', 20)

        sheet.merge_range(y_offset, 0, y_offset, 3, _('Sale Analysis Report'), format0)
        y_offset += 1

        start_date = (datetime.strptime(date_from, '%Y-%m-%d') + relativedelta(hours=6, minutes=30)).strftime(
            '%Y-%m-%d')
        sheet.merge_range(y_offset, 0, y_offset, 1, _('Start Date:'), format1)
        sheet.merge_range(y_offset, 2, y_offset, 3, start_date, format1)
        y_offset += 1

        end_date = (datetime.strptime(date_to, '%Y-%m-%d') + relativedelta(hours=6, minutes=30)).strftime(
            '%Y-%m-%d')
        sheet.merge_range(y_offset, 0, y_offset, 1, _('End Date:'), format1)
        sheet.merge_range(y_offset, 2, y_offset, 3, end_date, format1)
        y_offset += 1

        sheet.merge_range(y_offset, 0, y_offset, 1, _('Analytic Account:'), format1)
        sheet.merge_range(y_offset, 2, y_offset, 3, analytic_name, format1)
        sheet.write('A5', 'Sr.', format1)
        sheet.write('B5', 'Order Date', format1)
        sheet.write('C5', 'Expected Date', format1)
        sheet.write('D5', 'Product Code (IF Code)', format1)
        sheet.write('E5', 'Product Name', format1)
        sheet.write('F5', 'Order No', format1)
        sheet.write('G5', 'Order Qty', format1)
        sheet.write('H5', 'Sale Price', format1)
        sheet.write('I5', 'Price Subtotal', format1)

        lines = self._get_data(data)
        sr_no = 1
        row_index = 6
        total_amount = 0
        for rec in lines:
            total_amount += rec.get('subtotal')
            sheet.write('A{}'.format(row_index), sr_no, format4)
            sheet.write('B{}'.format(row_index), rec.get('date'), format4)
            sheet.write('C{}'.format(row_index), rec.get('expected_date'), format4)
            sheet.write('D{}'.format(row_index), rec.get('product_code'), format4)
            sheet.write('E{}'.format(row_index), rec.get('product_name'), format7)
            sheet.write('F{}'.format(row_index), rec.get('order_no'), format7)
            sheet.write('G{}'.format(row_index), rec.get('order_qty'), format4)
            sheet.write('H{}'.format(row_index), rec.get('sale_price'), format5)
            sheet.write('I{}'.format(row_index), rec.get('subtotal'), format5)
            sr_no += 1
            row_index += 1
        sheet.merge_range(f'A{row_index}:H{row_index}', _('Net Total:'), format1)
        sheet.write('I{}'.format(row_index), total_amount or 0.00, format3)
