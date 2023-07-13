import pytz
import logging
from itertools import groupby
from odoo import api, models, fields
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)

OPENING_QUERY = """
SELECT	PRODUCT_ID, SUM(QTY) AS QTY
FROM(
        SELECT		PP.ID AS PRODUCT_ID, SUM(-PRODUCT_UOM_QTY) AS QTY
        FROM		PRODUCT_PRODUCT PP
                    LEFT JOIN STOCK_MOVE SM ON SM.PRODUCT_ID=PP.ID
                    LEFT JOIN STOCK_LOCATION LOC ON SM.LOCATION_ID=LOC.ID
        WHERE		SM.STATE='done' AND SM.DATE < %s AND LOC.USAGE='internal'
        GROUP BY	PP.ID
        UNION ALL   
        SELECT		PP.ID AS PRODUCT_ID, SUM(PRODUCT_UOM_QTY) AS QTY
        FROM		PRODUCT_PRODUCT PP
                    LEFT JOIN STOCK_MOVE SM ON SM.PRODUCT_ID=PP.ID
                    LEFT JOIN STOCK_LOCATION LOC ON SM.LOCATION_DEST_ID=LOC.ID
        WHERE		SM.STATE='done' AND SM.DATE < %s AND LOC.USAGE='internal'
        GROUP BY	PP.ID
) OPENING 
WHERE   PRODUCT_ID IN %s
GROUP   BY PRODUCT_ID
"""

QUERY = """

SELECT      {0},
            LOCATION_ID,
            SUM(ROUND(PURCHASE_QTY)) AS PURCHASE_QTY,
            SUM(ROUND(PURCHASE_RETURN_QTY)) AS PURCHASE_RETURN_QTY,
            SUM(ROUND(SALE_QTY)) AS SALE_QTY,
            SUM(ROUND(SALE_RETURN_QTY)) AS SALE_RETURN_QTY,
            SUM(ROUND(PRODUCTION_QTY)) AS PRODUCTION_QTY,
            SUM(ROUND(UNBUILD_QTY)) AS UNBUILD_QTY,
            SUM(ROUND(INTERNAL_TRANSFER_QTY)) AS INTERNAL_TRANSFER_QTY,
            SUM(ROUND(ADJUSTMENT_QTY)) AS ADJUSTMENT_QTY,
            SUM(ROUND(SCRAP_QTY)) AS SCRAP_QTY,
            SUM(ROUND(POS_QTY)) AS POS_QTY,
            SUM(ROUND(POS_RETURN_QTY)) AS POS_RETURN_QTY
            
FROM
(
SELECT      SML.PRODUCT_ID,
            PT.CATEG_ID AS CATEGORY_ID,
            CASE
                WHEN SL.USAGE='internal' THEN SL.ID
                WHEN DL.USAGE='internal' THEN DL.ID
                ELSE NULL
            END AS LOCATION_ID,
            CASE
                WHEN SM.PURCHASE_LINE_ID IS NOT NULL AND SL.USAGE='supplier' AND DL.USAGE='internal' AND DL.ID IN {1}
                THEN (SML.QTY_DONE / L_UOM.FACTOR) * P_UOM.FACTOR
                ELSE 0
            END AS PURCHASE_QTY,
            CASE
                WHEN SM.PURCHASE_LINE_ID IS NOT NULL AND SL.USAGE='internal' AND DL.USAGE='supplier' AND SL.ID IN {2}
                THEN (-SML.QTY_DONE / L_UOM.FACTOR) * P_UOM.FACTOR
                ELSE 0
            END AS PURCHASE_RETURN_QTY,
            CASE
                WHEN SM.SALE_LINE_ID IS NOT NULL AND SL.USAGE='internal' AND DL.USAGE='customer' AND SL.ID IN {3}
                THEN (-SML.QTY_DONE / L_UOM.FACTOR) * P_UOM.FACTOR
                ELSE 0
            END AS SALE_QTY,
            CASE
                WHEN SM.SALE_LINE_ID IS NOT NULL AND SL.USAGE='customer' AND DL.USAGE='internal' AND DL.ID IN {4}
                THEN (SML.QTY_DONE / L_UOM.FACTOR) * P_UOM.FACTOR
                ELSE 0
            END AS SALE_RETURN_QTY,
            
            
            CASE
                    WHEN SL.USAGE='internal' AND DL.USAGE='production' AND SM.RAW_MATERIAL_PRODUCTION_ID IS NOT NULL 
                    THEN -SM.PRODUCT_UOM_QTY
                    WHEN SL.USAGE='production' AND DL.USAGE='internal' AND sm.PRODUCTION_ID IS NOT NULL 
                    THEN SM.PRODUCT_UOM_QTY 
                    ELSE 0
                END
            AS PRODUCTION_QTY,
            
             CASE
                    WHEN SL.USAGE='internal' AND DL.USAGE='production' AND SM.UNBUILD_ID IS NOT NULL 
                    THEN -SM.PRODUCT_UOM_QTY
                    WHEN SL.USAGE='production' AND DL.USAGE='internal' AND sm.UNBUILD_ID IS NOT NULL 
                    THEN SM.PRODUCT_UOM_QTY 
                    ELSE 0
                END
            AS UNBUILD_QTY,
            CASE
                WHEN SL.USAGE='internal' AND DL.USAGE='internal' AND SL.ID IN {5}
                THEN (-SML.QTY_DONE / L_UOM.FACTOR) * P_UOM.FACTOR
                ELSE 0
            END AS INTERNAL_TRANSFER_QTY,
            CASE
                WHEN SL.USAGE='inventory' AND DL.USAGE='internal' AND SM.SCRAPPED!=TRUE AND DL.ID IN {6} AND SM.STOCK_REPACKAGING_LINE_ID IS NULL AND SM.STOCK_PACKAGING_LINE_ID IS NULL
                THEN (SML.QTY_DONE / L_UOM.FACTOR) * P_UOM.FACTOR
                WHEN SL.USAGE='internal' AND DL.USAGE='inventory' AND SM.SCRAPPED!=TRUE AND SL.ID IN {7} AND SM.STOCK_REPACKAGING_LINE_ID IS NULL AND SM.STOCK_PACKAGING_LINE_ID IS NULL
                THEN (-SML.QTY_DONE / L_UOM.FACTOR) * P_UOM.FACTOR
                ELSE 0
            END AS ADJUSTMENT_QTY,
            CASE
                WHEN SL.SCRAP_LOCATION=TRUE AND DL.USAGE='internal' AND SM.SCRAPPED=TRUE AND DL.ID IN {8}
                THEN (SML.QTY_DONE / L_UOM.FACTOR) * P_UOM.FACTOR
                WHEN SL.USAGE='internal' AND DL.SCRAP_LOCATION=TRUE AND SM.SCRAPPED=TRUE AND SL.ID IN {9}
                THEN (-SML.QTY_DONE / L_UOM.FACTOR) * P_UOM.FACTOR
                ELSE 0
            END AS SCRAP_QTY,
            
            CASE
                WHEN SM.ANALYTIC_ACCOUNT_ID IS NOT NULL AND SL.USAGE='internal' AND DL.USAGE='customer' AND SL.ID IN {10}
                THEN (-SML.QTY_DONE / L_UOM.FACTOR) * P_UOM.FACTOR
                ELSE 0
            END AS POS_QTY,
            CASE
                WHEN SM.ANALYTIC_ACCOUNT_ID IS NOT NULL AND SL.USAGE='customer' AND DL.USAGE='internal' AND DL.ID IN {11}
                THEN (SML.QTY_DONE / L_UOM.FACTOR) * P_UOM.FACTOR
                ELSE 0
            END AS POS_RETURN_QTY
            
FROM        STOCK_MOVE_LINE SML
            LEFT JOIN STOCK_MOVE SM ON SML.MOVE_ID=SM.ID
            LEFT JOIN STOCK_LOCATION SL ON SL.ID=SML.LOCATION_ID
            LEFT JOIN STOCK_LOCATION DL ON DL.ID=SML.LOCATION_DEST_ID
            LEFT JOIN PRODUCT_PRODUCT PP ON PP.ID=SM.PRODUCT_ID
            LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID=PP.PRODUCT_TMPL_ID
            LEFT JOIN PRODUCT_CATEGORY PC ON PC.ID=PT.CATEG_ID
            LEFT JOIN UOM_UOM P_UOM ON P_UOM.ID=PT.UOM_ID
            LEFT JOIN UOM_UOM L_UOM ON L_UOM.ID=SML.PRODUCT_UOM_ID
            
WHERE       SML.DATE >= '{12}' AND SML.DATE <= '{13}' AND SML.STATE='done' AND SML.PRODUCT_ID IN {14}
            AND (SL.ID IN {15} OR DL.ID IN {16})
            
UNION ALL

SELECT      SML.PRODUCT_ID,
            PT.CATEG_ID AS CATEGORY_ID,
            SML.LOCATION_DEST_ID AS LOCATION_ID,
            0 AS PURCHASE_QTY,
            0 AS PURCHASE_RETURN_QTY,
            0 AS SALE_QTY,
            0 AS SALE_RETURN_QTY,
            0 AS PRODUCTION_QTY,
            0 AS UNBUILD_QTY,
            (SML.QTY_DONE / L_UOM.FACTOR) * P_UOM.FACTOR AS INTERNAL_TRANSFER_QTY,
            0 AS ADJUSTMENT_QTY,
            0 AS SCRAP_QTY,
            0 AS POS_QTY,
            0 AS POS_RETURN_QTY

FROM        STOCK_MOVE_LINE SML
            LEFT JOIN STOCK_MOVE SM ON SML.MOVE_ID=SM.ID
            LEFT JOIN STOCK_LOCATION SL ON SL.ID=SML.LOCATION_ID
            LEFT JOIN STOCK_LOCATION DL ON DL.ID=SML.LOCATION_DEST_ID
            LEFT JOIN PRODUCT_PRODUCT PP ON PP.ID=SM.PRODUCT_ID
            LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID=PP.PRODUCT_TMPL_ID
            LEFT JOIN PRODUCT_CATEGORY PC ON PC.ID=PT.CATEG_ID
            LEFT JOIN UOM_UOM P_UOM ON P_UOM.ID=PT.UOM_ID
            LEFT JOIN UOM_UOM L_UOM ON L_UOM.ID=SML.PRODUCT_UOM_ID
            
WHERE       SML.DATE >= '{17}' AND SML.DATE <= '{18}' AND SML.STATE='done' AND SML.PRODUCT_ID IN {19}
            AND SL.USAGE='internal' AND DL.USAGE='internal' AND DL.ID IN {20}

) AS DATA

GROUP BY LOCATION_ID, {21}

ORDER BY LOCATION_ID
"""


class StockInOutReport(models.AbstractModel):
    _name = 'report.stock_in_out_report.stock_in_out_report'
    _description = 'Stock I/O Report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objects):
        tz = pytz.timezone(self.env.context.get('tz'))
        start_date_raw = datetime.strptime(data['start_date'], DEFAULT_SERVER_DATE_FORMAT)
        end_date_raw = datetime.strptime(data['end_date'] + ' 23:59:59', DEFAULT_SERVER_DATETIME_FORMAT)
        start_date = tz.localize(start_date_raw).astimezone(pytz.utc)
        end_date = tz.localize(end_date_raw).astimezone(pytz.utc)
        warehouse_ids = self.env['stock.warehouse'].browse(data['warehouse_ids'])
        location_ids = self.env['stock.location'].browse(data['location_ids'])
        category_ids = self.env['product.category'].browse(data['category_ids'])
        product_ids = self.env['product.product'].browse(data['product_ids'])
        based_on = data['based_on']

        sheet = workbook.add_worksheet('Stock In/Out Report')
        topmost_cell = workbook.add_format({
            'font_name': 'Arial', 'font_size': 11,
            'valign': 'vcenter', 'align': 'center', 'bold': True,
        })
        header_cell = workbook.add_format({
            'font_name': 'Arial', 'font_size': 10, 'text_wrap': True,
            'valign': 'vcenter', 'align': 'center', 'bold': True, 'border': 1,
        })
        header_cell_left = workbook.add_format({
            'font_name': 'Arial', 'font_size': 10,
            'valign': 'vcenter', 'align': 'left', 'bold': True, 'border': 1,
        })

        sheet.merge_range('A1:AF1', 'Stock Detail Report By Locations', topmost_cell)
        sheet.merge_range('A3:B3', 'Company', header_cell_left)
        sheet.merge_range('C3:D3', self.env.company.name, header_cell_left)
        sheet.merge_range('A4:B4', 'Warehouse', header_cell_left)
        sheet.merge_range('C4:D4', ', '.join(warehouse_ids.mapped('name')), header_cell_left)
        sheet.merge_range('A5:B5', 'Location', header_cell_left)
        sheet.merge_range('C5:D5', ', '.join(location_ids.mapped('complete_name')), header_cell_left)
        sheet.merge_range('A6:B6', 'Beginning Date', header_cell_left)
        sheet.merge_range('C6:D6', start_date_raw.strftime('%d %B, %Y'), header_cell_left)
        sheet.merge_range('A7:B7', 'Ending Date', header_cell_left)
        sheet.merge_range('C7:D7', end_date_raw.strftime('%d %B, %Y'), header_cell_left)

        sheet.set_column('A:A', 5)
        sheet.set_column('B:B', 25)
        sheet.set_column('C:C', 15)
        sheet.set_column('D:D', 40)
        sheet.set_column('E:E', 10)
        sheet.set_column('F:F', 15)
        sheet.set_column('G:G', 10)
        sheet.set_column('AH:AH', 10)
        sheet.set_column('AI:AI', 15)
        sheet.set_column('AJ:AJ', 10)
        sheet.set_column('AA:AB', 10)
        sheet.set_column('AC:AD', 10)
        sheet.set_column('AE:AF', 10)

        sheet.merge_range(f'A9:A10', 'No.', header_cell)
        sheet.merge_range(f'B9:B10', 'Product', header_cell)
        sheet.merge_range(f'C9:C10', 'Internal Ref', header_cell)
        sheet.merge_range(f'D9:D10', 'Category', header_cell)
        sheet.merge_range(f'E9:F9', 'Opening', header_cell)
        sheet.merge_range(f'G9:H9', 'Purchase', header_cell)
        sheet.merge_range(f'I9:J9', 'Purchase Return', header_cell)
        sheet.merge_range(f'K9:L9', 'Sale', header_cell)
        sheet.merge_range(f'M9:N9', 'Sale Return', header_cell)
        sheet.merge_range(f'O9:P9', 'Point of Sale', header_cell)
        sheet.merge_range(f'Q9:R9', 'Point of Sale Return', header_cell)
        sheet.merge_range(f'S9:T9', 'Production', header_cell)
        sheet.merge_range(f'U9:V9', 'Unbuild', header_cell)
        sheet.merge_range(f'W9:X9', 'Adjustment', header_cell)
        sheet.merge_range(f'Y9:Z9', 'Internal Transfer', header_cell)
        sheet.merge_range(f'AA9:AB9', 'Scrap', header_cell)
        sheet.merge_range(f'AC9:AD9', 'Repackaging', header_cell)
        sheet.merge_range(f'AE9:AF9', 'Unpackaging', header_cell)
        sheet.merge_range(f'AG9:AH9', 'Closing', header_cell)

        row_index = 10
        columns = [
            ('E', 'F'), ('G', 'H'), ('I', 'J'), ('K', 'L'), ('M', 'N'),
            ('O', 'P'), ('Q', 'R'), ('S', 'T'), ('U', 'V'), ('W', 'X'),
            ('Y', 'Z'), ('AA', 'AB'), ('AC', 'AD'), ('AE', 'AF'),('AG', 'AH')
        ]
        for col_group in columns:
            sheet.set_column(f'{col_group[0]}:{col_group[0]}', 10)
            sheet.set_column(f'{col_group[1]}:{col_group[1]}', 15)
            sheet.write(f'{col_group[0]}{row_index}', 'Qty', header_cell)
            sheet.write(f'{col_group[1]}{row_index}', 'Qty (UoM)', header_cell)

        if not product_ids:
            product_ids = self.env['product.product'].search([('detailed_type', '=', 'product')])
        group_by_str = 'PRODUCT_ID'

        locations_str = '(' + ', '.join([str(loc.id) for loc in location_ids]) + ')'
        products_str = '(' + ', '.join([str(product.id) for product in product_ids]) + ')'
        query = QUERY.format(group_by_str,
                             locations_str,
                             locations_str,
                             locations_str,
                             locations_str,
                             locations_str,
                             locations_str,
                             locations_str,
                             locations_str,
                             locations_str,
                             locations_str,
                             locations_str,
                             start_date.strftime('%Y-%m-%d %H:%M:%S'),
                             end_date.strftime('%Y-%m-%d %H:%M:%S'),
                             products_str,
                             locations_str,
                             locations_str,
                             start_date.strftime('%Y-%m-%d %H:%M:%S'),
                             end_date.strftime('%Y-%m-%d %H:%M:%S'),
                             products_str,
                             locations_str,
                             group_by_str)

        _logger.info(f'\n{query}\n')
        self.env.cr.execute(query)
        result = self.env.cr.dictfetchall()

        self.env.cr.execute(OPENING_QUERY, (start_date_raw, end_date_raw, tuple(product_ids.ids)))

        opening_product_ids = self.env.cr.dictfetchall()

        product_ids = data.get('product_ids')
        transaction_product = []
        for rec in result:
            transaction_product.append(
                rec.get('product_id')
            )
        no_transaction_products = set(product_ids) - set(transaction_product)
        for location_id in location_ids:
            for no_transaction_product in no_transaction_products:
                result.append({
                    'product_id': no_transaction_product,
                    'location_id': location_id.id,
                    'purchase_qty': 0.0,
                    'purchase_return_qty': 0.0,
                    'sale_qty': 0.0,
                    'sale_return_qty': 0.0,
                    'production_qty': 0.0,
                    'unbuild_qty': 0.0,
                    'internal_transfer_qty': 0.0,
                    'adjustment_qty': 0.0,
                    'scrap_qty': 0.0,
                    'pos_qty': 0.0,
                    'pos_return_qty': 0.0,
                    'no_transaction': True,
                })

        if result:
            sorted_result = sorted(result, key=lambda x: x['location_id'])
            grouped_records = groupby(sorted_result, lambda rec: rec['location_id'])
            self.group_by_products(workbook, sheet, grouped_records, start_date_raw, end_date_raw, location_ids,
                                   opening_product_ids)

    def group_by_products(self, workbook, sheet, grouped_records, start_date_raw, end_date_raw, allowed_locations,
                          opening_product_ids):
        row_index = 11
        normal_center_cell = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9, 'border': 1,
            'valign': 'vcenter', 'align': 'center','num_format': '#,##0.00'
        })
        normal_left_cell = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9, 'border': 1,'num_format': '#,##0.00',
            'valign': 'vcenter', 'align': 'left'
        })
        top_center_cell = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9,
            'valign': 'vcenter', 'align': 'center', 'bold': True,
            'top': 1, 'bottom': 2, 'left': 1, 'right': 1,'num_format': '#,##0.00'
        })

        for location, records in grouped_records:
            location_name = self.env['stock.location'].browse(location).complete_name
            number = 1
            location_line_index = row_index
            row_index += 1
            location = self.env['stock.location'].browse(location)
            total_production_qty = total_unbuild_qty = total_unpackaging_qty = total_repackaging_qty = 0
            total_purchase_qty = total_purchase_return_qty = total_sale_qty = total_sale_return_qty = total_pos_qty = total_pos_return_qty = 0
            total_internal_transfer_qty = total_adjustment_qty = total_scrap_qty = total_opening_qty = total_closing_qty = 0
            if location.id not in allowed_locations.ids:
                continue

            for record in records:

                product = self.env['product.product'].browse(record['product_id'])

                no_transaction = False

                if record.get('no_transaction'):
                    no_transaction = record.get('no_transaction')

                if no_transaction:
                    opening_qty = self.env['stock.backdate.report'].with_context(inventory_date=start_date_raw).search([
                        ('product_id', '=', product.id),
                        ('location_id', '=', location.id),
                    ]).on_hand_qty
                else:
                    opening_qty = self.env['stock.backdate.report'].with_context(inventory_date=start_date_raw).search(
                        [('product_id', '=', product.id), ('location_id', '=', location.id)]).on_hand_qty


                unpackaging_product = self.env['stock.repackaging.line'].search(
                    [('product_id', '=', product.id), ('repackaging_id.state', '=', 'done'),
                     ('repackaging_id.date', '>=', start_date_raw), ('repackaging_id.date', '<=', end_date_raw),
                     ('repackaging_id.location_id', '=', location.id)])

                repackaging_product = self.env['stock.packaging.line'].search(
                    [('product_id', '=', product.id), ('stock_package_id.state', '=', 'done'),
                     ('stock_package_id.date', '>=', start_date_raw),
                     ('stock_package_id.date', '<=', end_date_raw), ('stock_package_id.location_id', '=', location.id)])

                unpackaging_quantity = repackaging_quantity = 0
                if unpackaging_product:
                    unpackaging_quantity = sum(
                        unpackaging_product.filtered(lambda m: m.product_id.id == product.id).mapped("quantity"))
                if repackaging_product:
                    repackaging_quantity = sum(
                        repackaging_product.filtered(lambda m: m.product_id.id == product.id).mapped("qty"))

                purchase_qty = record['purchase_qty']
                purchase_return_qty = record['purchase_return_qty']
                sale_qty = record['sale_qty']
                sale_return_qty = record['sale_return_qty']
                internal_transfer_qty = record['internal_transfer_qty']
                adjustment_qty = record['adjustment_qty']
                production_qty = record['production_qty']
                unbuild_qty = record['unbuild_qty']
                pos_qty = record['pos_qty']
                pos_return_qty = record['pos_return_qty']
                scrap_qty = record['scrap_qty']
                closing_qty = opening_qty + purchase_qty + purchase_return_qty + sale_qty + sale_return_qty + pos_qty + pos_return_qty + production_qty + unbuild_qty + adjustment_qty + scrap_qty + repackaging_quantity + unpackaging_quantity + internal_transfer_qty

                sheet.write(f'A{row_index}', number, normal_center_cell)
                sheet.write(f'B{row_index}', product.name, normal_left_cell)
                sheet.write(f'C{row_index}', product.default_code or '-', normal_center_cell)
                sheet.write(f'D{row_index}', product.categ_id.complete_name, normal_center_cell)

                sheet.write(f'E{row_index}', opening_qty, normal_center_cell)
                sheet.write(f'F{row_index}', product.product_tmpl_id.convert_to_multi_uom(opening_qty),
                            normal_center_cell)
                sheet.write(f'G{row_index}', purchase_qty, normal_center_cell)
                sheet.write(f'H{row_index}', product.product_tmpl_id.convert_to_multi_uom(purchase_qty) or '',
                            normal_center_cell)
                sheet.write(f'I{row_index}', purchase_return_qty, normal_center_cell)
                sheet.write(f'J{row_index}', product.product_tmpl_id.convert_to_multi_uom(purchase_return_qty),
                            normal_center_cell)
                sheet.write(f'K{row_index}', sale_qty, normal_center_cell)
                sheet.write(f'L{row_index}', product.product_tmpl_id.convert_to_multi_uom(sale_qty), normal_center_cell)
                sheet.write(f'M{row_index}', sale_return_qty, normal_center_cell)

                sheet.write(f'N{row_index}', product.product_tmpl_id.convert_to_multi_uom(sale_return_qty),
                            normal_center_cell)
                sheet.write(f'O{row_index}', pos_qty, normal_center_cell)
                sheet.write(f'P{row_index}', product.product_tmpl_id.convert_to_multi_uom(pos_qty), normal_center_cell)
                sheet.write(f'Q{row_index}', pos_return_qty, normal_center_cell)
                sheet.write(f'R{row_index}', product.product_tmpl_id.convert_to_multi_uom(pos_return_qty),
                            normal_center_cell)
                sheet.write(f'S{row_index}', production_qty, normal_center_cell)
                sheet.write(f'T{row_index}', product.product_tmpl_id.convert_to_multi_uom(production_qty),
                            normal_center_cell)
                sheet.write(f'U{row_index}', unbuild_qty, normal_center_cell)
                sheet.write(f'V{row_index}', product.product_tmpl_id.convert_to_multi_uom(unbuild_qty),
                            normal_center_cell)

                sheet.write(f'W{row_index}', adjustment_qty, normal_center_cell)
                sheet.write(f'X{row_index}', product.product_tmpl_id.convert_to_multi_uom(adjustment_qty),
                            normal_center_cell)
                sheet.write(f'Y{row_index}', internal_transfer_qty, normal_center_cell)
                sheet.write(f'Z{row_index}', product.product_tmpl_id.convert_to_multi_uom(internal_transfer_qty),
                            normal_center_cell)

                sheet.write(f'AA{row_index}', scrap_qty, normal_center_cell)
                sheet.write(f'AB{row_index}', product.product_tmpl_id.convert_to_multi_uom(scrap_qty),
                            normal_center_cell)
                sheet.write(f'AC{row_index}', repackaging_quantity, normal_center_cell)
                sheet.write(f'AD{row_index}', product.product_tmpl_id.convert_to_multi_uom(repackaging_quantity),
                            normal_center_cell)
                sheet.write(f'AE{row_index}', unpackaging_quantity, normal_center_cell)
                sheet.write(f'AF{row_index}', product.product_tmpl_id.convert_to_multi_uom(unpackaging_quantity),
                            normal_center_cell)
                sheet.write(f'AG{row_index}', closing_qty, normal_center_cell)
                sheet.write(f'AH{row_index}', product.product_tmpl_id.convert_to_multi_uom(closing_qty),
                            normal_center_cell)

                total_opening_qty += opening_qty
                total_purchase_qty += purchase_qty
                total_purchase_return_qty += purchase_return_qty
                total_sale_qty += sale_qty
                total_sale_return_qty += sale_return_qty
                total_internal_transfer_qty += internal_transfer_qty
                total_adjustment_qty += adjustment_qty
                total_pos_qty += pos_qty
                total_pos_return_qty += pos_return_qty
                total_production_qty += production_qty
                total_unbuild_qty += unbuild_qty
                total_repackaging_qty += repackaging_quantity
                total_unpackaging_qty += unpackaging_quantity
                total_scrap_qty += scrap_qty
                total_closing_qty += closing_qty
                row_index += 1
                number += 1
            sheet.write(f'A{location_line_index}', '', top_center_cell)
            sheet.write(f'B{location_line_index}', location.complete_name, top_center_cell)
            sheet.write(f'C{location_line_index}', '', top_center_cell)
            sheet.write(f'D{location_line_index}', 'Total', top_center_cell)
            sheet.write(f'E{location_line_index}', total_opening_qty, top_center_cell)
            sheet.write(f'G{location_line_index}', total_purchase_qty, top_center_cell)
            sheet.write(f'I{location_line_index}', total_purchase_return_qty, top_center_cell)
            sheet.write(f'K{location_line_index}', total_sale_qty, top_center_cell)
            sheet.write(f'M{location_line_index}', total_sale_return_qty, top_center_cell)
            sheet.write(f'O{location_line_index}', total_pos_qty, top_center_cell)
            sheet.write(f'Q{location_line_index}', total_pos_return_qty, top_center_cell)
            sheet.write(f'S{location_line_index}', total_production_qty, top_center_cell)
            sheet.write(f'U{location_line_index}', total_unbuild_qty, top_center_cell)
            sheet.write(f'W{location_line_index}', total_adjustment_qty, top_center_cell)
            sheet.write(f'Y{location_line_index}', total_internal_transfer_qty, top_center_cell)
            sheet.write(f'AA{location_line_index}', total_scrap_qty, top_center_cell)
            sheet.write(f'AC{location_line_index}', total_repackaging_qty, top_center_cell)
            sheet.write(f'AE{location_line_index}', total_unpackaging_qty, top_center_cell)
            sheet.write(f'AG{location_line_index}', total_closing_qty, top_center_cell)
            row_index += 1
