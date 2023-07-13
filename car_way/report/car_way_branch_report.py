import pytz
import logging
from itertools import groupby
from odoo import api, models, fields
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)

QUERY = """

SELECT              {0},
                    SM.ID,
                    SM.PRODUCT_QTY  QTY,
                    SM.PRODUCT_ID,
                    SM.PRODUCT_UOM UOM_ID,
                    SM.PRODUCT_PACKAGING_ID,
                    DATE(SP.SCHEDULED_DATE + INTERVAL '6 hours 30 minutes') AS EXPECTED_DATE,
                    SP.ANALYTIC_ACCOUNT_ID,
                    SP.CAR_WAY_ID ,
                    CWL.CAR_NAME AS CAR_NUMBER,
                    WSR.SALE_TYPE,
                    WSR.REFERENCE_NO AS REFERENCE_NO,
                    SM.REMARK,
                    SM.DISTRIBUTION_REMARK AS DISTRIBUTION_REMARK,
                    WSRL.PACKAGING_SIZE,
                    WSR.SALE_PICKING
            FROM
                  STOCK_PICKING SP
                  INNER JOIN STOCK_MOVE SM ON SP.ID = SM.PICKING_ID
                  INNER JOIN WHOLE_SALE_REQUISITION WSR ON WSR.ID = SP.SALE_REQUISITION_ID
                  INNER JOIN WHOLE_SALE_REQUISITION_LINE WSRL ON WSR.ID = WSRL.REQUISITION_ID AND WSRL.ID = SM.WS_REQ_LINE_ID
                  INNER JOIN CAR_WAY_NAME CWN ON SP.CAR_WAY_ID = CWN.ID
                  INNER JOIN CAR_WAY_LINE CWL ON CWL.WAY_NAME = CWN.ID
                  INNER JOIN CAR_WAY CW ON CW.ID=CWL.WAY_ID
                WHERE
                  SP.IS_GOOD_ISSUED = TRUE
                  AND WSRL.STATE = 'approved' 
                  AND SP.SALE_REQUISITION_ID IS NOT NULL
                  AND CW.DATE=DATE(SP.SCHEDULED_DATE + INTERVAL '6 hours 30 minutes')
                  AND  CW.DATE= '{0}'"""


class CarWayBranchReport(models.AbstractModel):
    _name = 'report.car_way.car_way_branch_report'
    _description = 'Car Way By Branch Report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objects):
        tz = pytz.timezone(self.env.context.get('tz'))
        analytic_account_id = self.env['account.analytic.account'].browse(data['analytic_account_id'])
        car_way_id = self.env['car.way.name'].browse(data['car_way_id'])
        date = datetime.strptime(data['date'], DEFAULT_SERVER_DATE_FORMAT)
        date_time = datetime.min.time()
        date_time1 = datetime.combine(date, date_time)
        delta = relativedelta(hours=23, minutes=59)

        date_time_str = date_time1.strftime("%Y-%m-%d %H:%M:%S")
        date_to_str = (datetime.strptime(data['date'], DEFAULT_SERVER_DATE_FORMAT) + delta).strftime(
            DEFAULT_SERVER_DATETIME_FORMAT)

        sheet = workbook.add_worksheet('Car Way By Branches')
        topmost_cell = workbook.add_format({
            'font_name': 'Arial', 'font_size': 12,
            'valign': 'vcenter', 'align': 'left', 'bold': True,
        })
        topmost_cell1 = workbook.add_format({
            'font_name': 'Arial', 'font_size': 10,
            'valign': 'vcenter', 'align': 'left', 'bold': True,
        })
        header_cell = workbook.add_format({
            'bold': True, 'border': True, 'align': 'center', 'font_size': 13, 'valign': 'vcenter',
        })
        header_cell_main = workbook.add_format({
            'font_name': 'Arial', 'font_size': 11,
            'valign': 'vcenter', 'align': 'center', 'bold': True, 'border': 1, 'bg_color': '#696969', 'color': 'white',
        })

        cell_style = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9,
            'valign': 'vcenter', 'align': 'center', 'right': 1, 'color': 'black', 'border': True,
        })
        cell_style1 = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9,
            'valign': 'vcenter', 'align': 'left', 'right': 1, 'color': 'black', 'border': 1,
        })
        date_format = 'Date' + '       - ' + str(date.strftime("%d")) + '-' + str(date.strftime("%m")) + '-' + str(
            date.strftime("%Y"))
        shop_name = ''
        sheet.set_row(0, 25)
        sheet.set_row(1, 20)
        sheet.set_row(2, 20)
        sheet.set_column('A:A', 30)
        sheet.set_column('B:B', 55)
        sheet.set_column('C:C', 25)
        sheet.set_column('D:D', 20)
        sheet.set_column('E:E', 40)
        sheet.set_column('F:F', 40)
        car_way_name = "Car Way - " + car_way_id.name

        car_number = []
        car_no =''


        start_date = data['date']

        query = QUERY.format(start_date)
        _logger.info(f'\n{query}\n')
        self.env.cr.execute(query)
        result = self.env.cr.dictfetchall()
        car_way_datas = self.env['car.way'].search([('date', '=', data.get('expected_date'))])
        picking_ids = self.env['stock.picking'].search([('car_way_id', 'in', car_way_datas.ids)])
        # df = pd.DataFrame(result)
        # way_lines = df[(df['analytic_account_id'] == analytic_account_id.id) & (df['car_way_id'] == car_way_id.id)].to_dict('records')

        date = data['date']
        way_lines = [record for record in result if
                     record['analytic_account_id'] == analytic_account_id.id and record['car_way_id'] == car_way_id.id]
        sale_type = ''
        row_index = 6
        whole_row_index = 2
        retail_len = 1
        actual_len = 0
        total_len = 1
        total_whole_len = 2
        total_whole_qty = 0
        total_retail_qty = 0
        count_retail_sale = 0
        count_whole_sale = 0
        retail_list = []
        whole_sale_list = []
        move_id_list = []
        whole_move_id_list = []
        for rec in way_lines:
            if 'car_number' in rec and rec['car_number'] not in car_number:
                if rec['car_number']:
                    car_number.append(rec['car_number'])
            picking_time_str = rec.get('expected_date').strftime("%Y-%m-%d %H:%M:%S")
            if rec.get('sale_type') == 'retail_sale' and rec.get(
                    'id') not in move_id_list and rec.get('analytic_account_id') == analytic_account_id.id and rec.get(
                'car_way_id') == car_way_id.id:
                retail_list.append(rec)
                move_id_list.append(rec.get('id'))
            elif rec.get('sale_type') == 'whole_sale' and rec.get(
                    'id') not in whole_move_id_list and rec.get(
                'analytic_account_id') == analytic_account_id.id and rec.get('car_way_id') == car_way_id.id:
                whole_sale_list.append(rec)
                whole_move_id_list.append(rec.get('id'))
            else:
                pass

        for retail in retail_list:
            if retail.get('analytic_account_id') == analytic_account_id.id and retail.get('sale_type') == 'retail_sale':
                row_index += 1
                retail_len += 1
                count_retail_sale += 1
                product_package_id = self.env['stock.move'].browse(retail.get('id')).product_packaging_id
                sheet.write(('B6'), 'Retail Sale', header_cell_main)
                sheet.write(('D6'), 'QTY', header_cell_main)
                sheet.write('A{}'.format(row_index), retail.get('reference_no'), cell_style)
                product_data = self.env['product.product'].browse(retail.get('product_id'))

                sheet.write('B{}'.format(row_index), product_data.name, cell_style1)

                sheet.write('C{}'.format(row_index), product_package_id.name if product_package_id else '', cell_style)
                sheet.write('D{}'.format(row_index), retail.get('qty') if retail.get('qty') else 0, cell_style)
                sheet.write('E{}'.format(row_index), retail.get('distribution_remark') or '', cell_style)
                sheet.write('F{}'.format(row_index), retail.get('remark') or '', cell_style)

                if retail.get('qty'):
                    total_retail_qty += retail.get('qty')
        if total_len == 1:
            total_len += row_index
        if count_retail_sale != 0:
            sheet.write('C{}'.format(total_len), 'TOTAL QTY', header_cell)
            sheet.write('D{}'.format(total_len), total_retail_qty, header_cell)
        whole_row_index += row_index
        if len(retail_list) == 0:
            whole_row_index -= 3
        for whole in whole_sale_list:
            if whole.get('analytic_account_id') == analytic_account_id.id and whole.get('sale_type') == 'whole_sale':
                count_whole_sale += 1
                whole_row_index += 1
                product_package_id = self.env['stock.move'].browse(whole.get('id')).product_packaging_id
                if actual_len == 0:
                    actual_len = whole_row_index
                sheet.write('B{}'.format(actual_len), 'Whole Sale', header_cell_main)
                sheet.write('D{}'.format(actual_len), 'QTY', header_cell_main)
                sheet.write('A{}'.format(whole_row_index + 1), whole.get('reference_no'), cell_style)
                product_data = self.env['product.product'].browse(whole.get('product_id'))
                # packaging_data = self.env['product.packaging'].browse(whole.get('product_packaging_id'))
                sheet.write('B{}'.format(whole_row_index + 1), product_data.name, cell_style1)
                sheet.write('C{}'.format(whole_row_index + 1), product_package_id.name if product_package_id else '',
                            cell_style)
                sheet.write('D{}'.format(whole_row_index + 1), whole.get('qty') if whole.get('qty') else 0, cell_style)
                sheet.write('E{}'.format(whole_row_index + 1), whole.get('distribution_remark') or '', cell_style)
                sheet.write('F{}'.format(whole_row_index + 1), whole.get('remark') or '', cell_style)

                if whole.get('qty'):
                    total_whole_qty += whole.get('qty')

        if total_whole_len == 2:
            total_whole_len += whole_row_index
        if count_whole_sale != 0:
            sheet.write('C{}'.format(total_whole_len), 'TOTAL QTY', header_cell)
            sheet.write('D{}'.format(total_whole_len), total_whole_qty, header_cell)
        if car_number:
            car_data= ','.join(car_number)
            car_no = 'Car Number - '+ car_data
        sheet.merge_range(f'A{1}:B{1}', car_way_name, topmost_cell1)
        sheet.merge_range(f'A{2}:B{2}', date_format, topmost_cell1)
        sheet.merge_range(f'A{3}:B{3}', car_no, topmost_cell1)
        sheet.merge_range('C1:F1', 'Car Way Branch Report', topmost_cell)

        sheet.write('A4', 'Requisition Sequence', header_cell)
        sheet.write('B4', 'Sale Type', header_cell)
        sheet.write('C4', 'Packaging Type', header_cell)
        sheet.write('D4', analytic_account_id.name, header_cell)
        sheet.write('E4', 'Distribution Remark', header_cell)
        sheet.write('F4', 'Sale Requisition Remark', header_cell)
