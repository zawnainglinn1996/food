from collections import defaultdict

from odoo import models, fields, api, _
import pytz
from datetime import datetime
from dateutil import relativedelta
from dateutil.relativedelta import relativedelta
from itertools import groupby


class PosAnalysisExcelReport(models.AbstractModel):
    _name = 'report.pos_analysis_excel_report.pos_analysis_excel_report'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'POS Analysis Report'

    @api.model
    def _get_data(self, options):
        date_from = options.get('date_from')
        date_to = options.get('date_to')
        analytic_account_ids = options['analytic_account_id']

        domain = [('date_order', '>=', date_from), ('date_order', '<=', date_to),
                  ('state', 'not in', ['draft', 'cancel']),
                  ('analytic_account_id', 'in', analytic_account_ids)]

        order_ids = self.env['pos.order'].search(domain)
        order_line_ids = []

        for order in order_ids:
            for line in order.lines:
                order_date = line.order_id.date_order.strftime('%Y-%m-%d')
                order_line_ids.append({
                    'order_id': line.order_id.id,
                    'product_code': line.product_id.default_code or '',
                    'product_name': line.product_id.name or '',
                    'product_id': line.product_id.id,
                    'order_qty': line.qty or 0.00,
                    'sale_price': line.price_unit or 0.00,
                    'subtotal': line.price_subtotal_incl or 0.00,
                })
        return order_line_ids

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
            'bg_color': '#B0C4DE', 'valign': 'vcenter', 'border': True,
        })

        format1 = workbook.add_format({
            'bold': True, 'border': True, 'align': 'center', 'font_size': 13, 'valign': 'vcenter',
        })

        format3 = workbook.add_format({
            'bold': False, 'border': True, 'align': 'right', 'font_size': 12, 'valign': 'vcenter','num_format': '#,##0.00'
        })
        format4 = workbook.add_format({
            'align': 'center', 'border': True, 'valign': 'vcenter', 'font_size': 12, 'num_format': '#,##0.00'
        })
        format5 = workbook.add_format({
            'align': 'left', 'border': True, 'bold': False, 'font_size': 12, 'num_format': '#,##0.00',
            'valign': 'vcenter', })
        format6 = workbook.add_format({
            'bold': True, 'border': True, 'align': 'center', 'font_size': 12, 'valign': 'vcenter',
            'num_format': '#,##0.00'
        })

        format7 = workbook.add_format({
            'bold': True, 'border': True, 'align': 'right', 'font_size': 12, 'valign': 'vcenter',
            'num_format': '#,##0.00'
        })

        sheet = workbook.add_worksheet('POS Analysis Report')
        sheet.set_row(0, 30)
        sheet.set_row(1, 25)
        sheet.set_row(2, 25)
        sheet.set_row(3, 25)
        sheet.set_row(4, 25)

        sheet.set_column('A:A', 7)
        sheet.set_column('B:B', 26)
        sheet.set_column('C:C', 48)
        sheet.set_column('D:D', 15)
        sheet.set_column('E:E', 15)
        sheet.set_column('F:F', 20)
        sheet.set_column('G:G', 20)
        sheet.set_column('H:H', 20)
        sheet.set_column('I:I', 17)
        sheet.set_column('J:K', 20)

        sheet.merge_range(y_offset, 0, y_offset, 3, _('POS Analysis Report'), format0)
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
        sheet.write('B5', 'Product Code (IF Code)', format1)
        sheet.write('C5', 'Product Name', format1)
        sheet.write('D5', 'Order Qty', format1)
        sheet.write('E5', 'Sale Price', format1)
        sheet.write('F5', 'Price Subtotal', format1)

        lines = self._get_data(data)
        product_totals = defaultdict(lambda: {'total_order_qty': 0, 'total_subtotal': 0})

        for item in lines:
            product_totals[item['product_id']]['total_order_qty'] += item['order_qty']
            product_totals[item['product_id']]['total_subtotal'] += item['subtotal']
        pos_line_data = []
        for product, totals in product_totals.items():
            product_id = self.env['product.product'].browse(product)
            pos_line_data.append({
                'product_id': product,
                'category_id': product_id.categ_id.id,
                'total_order_quantity': totals['total_order_qty'],
                'total_subtotal': totals['total_subtotal']
            })

        row_index = 6
        total_amount = 0

        sorted_pos_order_lines = sorted(pos_line_data, key=lambda x: x['category_id'])
        grouped_records = groupby(sorted_pos_order_lines, lambda rec: rec['category_id'])

        for category, records in grouped_records:
            category_line_index = row_index
            sr_no = 1
            row_index += 1
            category_id = self.env['product.category'].browse(category)
            total_qty = total_sale_price = subtotal_amt = 0

            for rec in records:
                product_id = self.env['product.product'].browse(rec['product_id'])
                total_qty += rec.get('total_order_quantity')
                total_sale_price += product_id.list_price
                subtotal_amt += rec.get('total_subtotal')
                total_amount += rec.get('total_subtotal')
                sheet.write('A{}'.format(row_index), sr_no, format4)
                sheet.write('B{}'.format(row_index), product_id.default_code or '-', format4)
                sheet.write('C{}'.format(row_index), product_id.name, format5)
                sheet.write('D{}'.format(row_index), rec.get('total_order_quantity'), format4)
                sheet.write('E{}'.format(row_index), product_id.list_price, format3)
                sheet.write('F{}'.format(row_index), rec.get('total_subtotal'), format3)

                sr_no += 1
                row_index += 1
            sheet.write(f'A{category_line_index}', '', format1)
            sheet.write(f'B{category_line_index}', category_id.name, format1)
            sheet.write(f'C{category_line_index}', 'Total', format6)
            sheet.write(f'D{category_line_index}', total_qty, format6)
            sheet.write(f'E{category_line_index}', total_sale_price, format7)
            sheet.write(f'F{category_line_index}', subtotal_amt, format7)
        sheet.merge_range(f'A{row_index}:E{row_index}', _('Net Total:'), format1)
        sheet.write('F{}'.format(row_index), total_amount or 0.0, format7)
