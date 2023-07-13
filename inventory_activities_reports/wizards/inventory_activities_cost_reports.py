import pytz
import logging
from itertools import groupby
from odoo import api, models, fields, _
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

VALUATION_AMT_QUERY = """
SELECT  SVL.PRODUCT_ID, SUM(SVL.VALUE) AMT
FROM	STOCK_VALUATION_LAYER SVL
WHERE	SVL.CREATE_DATE < %s AND SVL.PRODUCT_ID IN %s
GROUP   BY SVL.PRODUCT_ID
"""

QUERY = """

SELECT		PP.ID AS PRODUCT_ID,
            SUM(
                CASE
                    WHEN SL.USAGE='supplier' AND DL.USAGE='internal' AND SM.PURCHASE_LINE_ID IS NOT NULL
                    THEN SM.PRODUCT_UOM_QTY ELSE 0
                END
            ) AS PURCHASE_QTY,
            SUM(
                CASE
                    WHEN SL.USAGE='supplier' AND DL.USAGE='internal' AND SM.PURCHASE_LINE_ID IS NOT NULL
                    THEN (SELECT SUM(VALUE) FROM STOCK_VALUATION_LAYER WHERE STOCK_MOVE_ID=SM.ID AND STOCK_VALUATION_LAYER_ID IS NULL)
                ELSE 0
                END
            ) AS PURCHASE_AMT,
            SUM(
                CASE
                    WHEN (SL.USAGE='internal' AND DL.USAGE='supplier' AND SM.PURCHASE_LINE_ID IS NOT NULL) OR
                         (SL.USAGE='internal' AND DL.USAGE='customer' AND SM.SALE_LINE_ID IS NULL)
                    THEN -SM.PRODUCT_UOM_QTY ELSE 0
                    END
            ) AS PURCHASE_RETURN_QTY,
            SUM(
                CASE
                    WHEN (SL.USAGE='internal' AND DL.USAGE='supplier' AND SM.PURCHASE_LINE_ID IS NOT NULL) OR
                         (SL.USAGE='internal' AND DL.USAGE='customer' AND SM.SALE_LINE_ID IS NULL)
                    THEN (SELECT SUM(VALUE) FROM STOCK_VALUATION_LAYER WHERE STOCK_MOVE_ID=SM.ID AND STOCK_VALUATION_LAYER_ID IS NULL)
                END
            ) AS PURCHASE_RETURN_AMT,
            SUM(
                CASE	
                    WHEN SL.USAGE='internal' AND DL.USAGE='customer' AND SM.SALE_LINE_ID IS NOT NULL
                    THEN -SM.PRODUCT_UOM_QTY ELSE 0
                END
            ) AS SALE_QTY,
            SUM(
                CASE
                    WHEN SL.USAGE='internal' AND DL.USAGE='customer' AND SM.SALE_LINE_ID IS NOT NULL
                    THEN (SELECT SUM(VALUE) FROM STOCK_VALUATION_LAYER WHERE STOCK_MOVE_ID=SM.ID AND STOCK_VALUATION_LAYER_ID IS NULL)
                END
            ) AS SALE_AMT,
            SUM(
                CASE	
                    WHEN (SL.USAGE='customer' AND DL.USAGE='internal' AND SM.SALE_LINE_ID IS NOT NULL) OR
                         (SL.USAGE='supplier' AND DL.USAGE='internal' AND SM.PURCHASE_LINE_ID IS NULL)
                    THEN SM.PRODUCT_UOM_QTY ELSE 0
                END
            ) AS SALE_RETURN_QTY,
            SUM(
                CASE
                    WHEN (SL.USAGE='customer' AND DL.USAGE='internal' AND SM.SALE_LINE_ID IS NOT NULL) OR
                         (SL.USAGE='supplier' AND DL.USAGE='internal' AND SM.PURCHASE_LINE_ID IS NULL)
                    THEN (SELECT SUM(VALUE) FROM STOCK_VALUATION_LAYER WHERE STOCK_MOVE_ID=SM.ID AND STOCK_VALUATION_LAYER_ID IS NULL)
                END
            ) AS SALE_RETURN_AMT,  
            SUM(
                CASE
                    WHEN SM.ANALYTIC_ACCOUNT_ID IS NOT NULL AND SL.USAGE='internal' AND DL.USAGE='customer'
                    THEN -SM.PRODUCT_UOM_QTY ELSE 0
                END 
            ) AS POS_QTY,
            SUM(
                CASE
                    WHEN SM.ANALYTIC_ACCOUNT_ID IS NOT NULL AND SL.USAGE='internal' AND DL.USAGE='customer'
                    THEN (SELECT SUM(VALUE) FROM STOCK_VALUATION_LAYER WHERE STOCK_MOVE_ID=SM.ID AND STOCK_VALUATION_LAYER_ID IS NULL)
                END 
            ) AS POS_AMT,
            SUM(
                CASE
                    WHEN SM.ANALYTIC_ACCOUNT_ID IS NOT NULL AND SL.USAGE='customer' AND DL.USAGE='internal'
                    THEN SM.PRODUCT_UOM_QTY ELSE 0
                END
            ) AS POS_RETURN_QTY,
            SUM(
                CASE
                    WHEN SM.ANALYTIC_ACCOUNT_ID IS NOT NULL AND SL.USAGE='customer' AND DL.USAGE='internal'
                    THEN (SELECT SUM(VALUE) FROM STOCK_VALUATION_LAYER WHERE STOCK_MOVE_ID=SM.ID AND STOCK_VALUATION_LAYER_ID IS NULL)
                END
            ) AS POS_RETURN_AMT,
            SUM(
                CASE
                    WHEN SL.USAGE='internal' AND DL.USAGE='production' AND SM.RAW_MATERIAL_PRODUCTION_ID IS NOT NULL 
                    THEN -SM.PRODUCT_UOM_QTY
                    WHEN SL.USAGE='production' AND DL.USAGE='internal' AND sm.PRODUCTION_ID IS NOT NULL 
                    THEN SM.PRODUCT_UOM_QTY 
                    ELSE 0
                END
            ) AS PRODUCTION_QTY,
            SUM(
                CASE
                    WHEN (SL.USAGE='internal' AND DL.USAGE='production' AND SM.RAW_MATERIAL_PRODUCTION_ID IS NOT NULL) 
                         OR 
                         (SL.USAGE='production' AND DL.USAGE='internal' AND sm.PRODUCTION_ID IS NOT NULL) 
                    THEN (SELECT SUM(VALUE) FROM STOCK_VALUATION_LAYER WHERE STOCK_MOVE_ID=SM.ID AND STOCK_VALUATION_LAYER_ID IS NULL)                        
                END
            ) AS PRODUCTION_AMT,
            SUM(
                CASE
                    WHEN SL.USAGE='internal' AND DL.USAGE='production' AND SM.UNBUILD_ID IS NOT NULL 
                    THEN -SM.PRODUCT_UOM_QTY
                    WHEN SL.USAGE='production' AND DL.USAGE='internal' AND sm.UNBUILD_ID IS NOT NULL 
                    THEN SM.PRODUCT_UOM_QTY 
                    ELSE 0
                END
            ) AS UNBUILD_QTY,
            SUM(
                CASE
                    WHEN (SL.USAGE='internal' AND DL.USAGE='production' AND SM.UNBUILD_ID IS NOT NULL) 
                         OR 
                         (SL.USAGE='production' AND DL.USAGE='internal' AND SM.UNBUILD_ID IS NOT NULL) 
                    THEN (SELECT SUM(VALUE) FROM STOCK_VALUATION_LAYER WHERE STOCK_MOVE_ID=SM.ID AND STOCK_VALUATION_LAYER_ID IS NULL)
                    ELSE 0
                END
            ) AS UNBUILD_AMT,
            SUM(
                CASE 
                    WHEN SM.SCRAPPED=TRUE THEN -SM.PRODUCT_UOM_QTY
                    ELSE 0
                END
            ) AS SCRAP_QTY,
            SUM(
                CASE 
                    WHEN SM.SCRAPPED=TRUE THEN (
                        SELECT 		SUM(VALUE) 
                        FROM 		STOCK_VALUATION_LAYER 
                        WHERE 		PRODUCT_ID=PP.ID AND STOCK_MOVE_ID=SM.ID AND STOCK_VALUATION_LAYER_ID IS NULL
                        GROUP BY 	STOCK_MOVE_ID
                    )
                    ELSE 0
                END
            ) AS SCRAP_AMT,
            SUM(
                CASE
                    WHEN SL.USAGE='inventory' AND DL.USAGE='internal' AND SL.SCRAP_LOCATION != TRUE
                    THEN SM.PRODUCT_UOM_QTY
                    WHEN SL.USAGE='internal' AND DL.USAGE='inventory' AND DL.SCRAP_LOCATION != TRUE
                    THEN -SM.PRODUCT_UOM_QTY
                    ELSE 0
                END
            ) AS ADJUSTMENT_QTY,
            SUM(
                CASE
                    WHEN (SL.USAGE='inventory' AND DL.USAGE='internal' AND SL.SCRAP_LOCATION != TRUE) OR 
                         (SL.USAGE='internal' AND DL.USAGE='inventory' AND DL.SCRAP_LOCATION != TRUE)
                    THEN (SELECT SUM(VALUE) FROM STOCK_VALUATION_LAYER WHERE STOCK_MOVE_ID=SM.ID AND STOCK_VALUATION_LAYER_ID IS NULL)
                END
            ) AS ADJUSTMENT_AMT

FROM		PRODUCT_PRODUCT PP
            LEFT JOIN STOCK_MOVE SM ON SM.PRODUCT_ID=PP.ID
            LEFT JOIN STOCK_LOCATION SL ON SM.LOCATION_ID=SL.ID
            LEFT JOIN STOCK_LOCATION DL ON SM.LOCATION_DEST_ID=DL.ID
            LEFT JOIN PURCHASE_ORDER_LINE POL ON SM.PURCHASE_LINE_ID=POL.ID
            LEFT JOIN SALE_ORDER_LINE SOL ON SM.SALE_LINE_ID=SOL.ID
            LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID=PP.PRODUCT_TMPL_ID
            LEFT JOIN UOM_UOM P_UOM ON P_UOM.ID=PT.UOM_ID
            LEFT JOIN UOM_UOM L_UOM ON L_UOM.ID=SM.PRODUCT_UOM

WHERE		SM.DATE >= '{}' AND SM.DATE < '{}' AND PP.ID IN {} AND SM.STATE='done'

GROUP BY 	PP.ID

"""


class InventoryActivitiesCostReportXlsx(models.AbstractModel):
    _name = 'report.inventory_activities_reports.activities_cost_xlsx'
    _description = 'Inventory Activities With Cost Report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objects):
        tz = pytz.timezone(self.env.context.get('tz'))
        start_date_raw = datetime.strptime(data['start_date'], DEFAULT_SERVER_DATE_FORMAT)
        end_date_raw = datetime.strptime(data['end_date'] + ' 23:59:59', DEFAULT_SERVER_DATETIME_FORMAT)
        start_date = tz.localize(start_date_raw).astimezone(pytz.utc)
        end_date = tz.localize(end_date_raw).astimezone(pytz.utc)
        product_ids = self.env['product.product'].browse(data['product_ids'])
        records = []
        sheet = workbook.add_worksheet('Inventory Activities With Cost Report')
        title = workbook.add_format({
            'font_name': 'Arial', 'font_size': 13, 'valign': 'vcenter', 'align': 'center', 'bold': True,
        })
        title_date = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9, 'valign': 'vcenter', 'align': 'center', 'bold': True, 'bottom': 1,
            'top': 1,
        })
        header = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9, 'valign': 'vcenter', 'align': 'center', 'bold': True, 'border': 1,
        })

        sheet.set_row(0, 25)

        sheet.set_column('A:A', 15)
        sheet.set_column('B:B', 30)
        sheet.set_column('C:C', 15)
        sheet.set_column('D:D', 8)
        sheet.set_column('E:F', 15)
        sheet.set_column('G:G', 8)
        sheet.set_column('H:I', 15)
        sheet.set_column('J:J', 8)
        sheet.set_column('K:L', 15)
        sheet.set_column('M:M', 8)
        sheet.set_column('N:O', 15)
        sheet.set_column('P:P', 8)
        sheet.set_column('Q:R', 15)
        sheet.set_column('S:S', 8)
        sheet.set_column('T:U', 15)
        sheet.set_column('V:V', 8)
        sheet.set_column('W:X', 15)
        sheet.set_column('Y:Y', 8)
        sheet.set_column('Z:AA', 15)
        sheet.set_column('AB:AB', 8)
        sheet.set_column('AC:AD', 15)
        sheet.set_column('AE:AE', 8)
        sheet.set_column('AF:AG', 15)
        sheet.set_column('AH:AH', 8)
        sheet.set_column('AI:AJ', 15)
        sheet.set_column('AK:AK', 8)
        sheet.set_column('AL:AL', 15)

        sheet.set_column('AM:AM', 15)
        sheet.set_column('AN:AN', 8)
        sheet.set_column('AO:AO', 15)

        sheet.set_column('AP:AP', 15)
        sheet.set_column('AQ:AQ', 8)
        sheet.set_column('AR:AR', 15)

        sheet.merge_range('A1:AL1', 'Stock Summary Report with Cost', title)
        sheet.merge_range('A2:AL2', '')
        sheet.write('A3', 'From Date:', title_date)
        sheet.write('B3', start_date_raw.strftime('%d %B, %Y'), title_date)
        sheet.write('A4', 'To Date:', title_date)
        sheet.write('B4', end_date_raw.strftime('%d %B, %Y'), title_date)
        sheet.merge_range('A5:AL5', '')

        sheet.write('A6', 'Item ID', header)
        sheet.write('B6', 'Item Description', header)

        sheet.write('C6', 'Opening Qty', header)
        sheet.write('D6', 'UOM', header)
        sheet.write('E6', 'Opening Cost', header)

        sheet.write('F6', 'Purchase Qty', header)
        sheet.write('G6', 'UOM', header)
        sheet.write('H6', 'Purchase Cost', header)

        sheet.write('I6', 'Purchase Return Qty', header)
        sheet.write('J6', 'UOM', header)
        sheet.write('K6', 'Purchase Return Cost', header)

        sheet.write('L6', 'Sale Qty', header)
        sheet.write('M6', 'UOM', header)
        sheet.write('N6', 'Sale Cost', header)

        sheet.write('O6', 'Sale Return Qty', header)
        sheet.write('P6', 'UOM', header)
        sheet.write('Q6', 'Sale Return Cost', header)

        sheet.write('R6', 'POS Qty', header)
        sheet.write('S6', 'UOM', header)
        sheet.write('T6', 'POS Cost', header)

        sheet.write('U6', 'POS Return Qty', header)
        sheet.write('V6', 'UOM', header)
        sheet.write('W6', 'POS Return Cost', header)

        sheet.write('X6', 'Production Qty', header)
        sheet.write('Y6', 'UOM', header)
        sheet.write('Z6', 'Production Cost', header)

        sheet.write('AA6', 'Unbuild Qty', header)
        sheet.write('AB6', 'UOM', header)
        sheet.write('AC6', 'Unbuild Cost', header)

        sheet.write('AD6', 'Adjustment Qty', header)
        sheet.write('AE6', 'UOM', header)
        sheet.write('AF6', 'Adjustment Cost', header)

        sheet.write('AG6', 'Scrap Qty', header)
        sheet.write('AH6', 'UOM', header)
        sheet.write('AI6', 'Scrap Cost', header)

        sheet.write('AJ6', 'Repackage Qty', header)
        sheet.write('AK6', 'UOM', header)
        sheet.write('AL6', 'Repackage Cost', header)

        sheet.write('AM6', 'Unpackaging Qty', header)
        sheet.write('AN6', 'UOM', header)
        sheet.write('AO6', 'Unpackaging Cost', header)

        sheet.write('AP6', 'Closing Qty', header)
        sheet.write('AQ6', 'UOM', header)
        sheet.write('AR6', 'Closing Cost', header)

        if not product_ids:
            product_ids = self.env['product.product'].search([('detailed_type', '=', 'product')])

        products_str = '(' + ', '.join([str(product.id) for product in product_ids]) + ')'

        date_from = datetime.combine(start_date_raw, datetime.min.time())
        date_to = datetime.combine(end_date_raw, datetime.min.time())
        date_from = date_from - relativedelta(hours=6, minutes=30)
        day_after_date_to = date_to + relativedelta(days=1, hours=-6, minutes=-30)

        query = QUERY.format(
            start_date.strftime('%Y-%m-%d %H:%M:%S'),
            end_date.strftime('%Y-%m-%d %H:%M:%S'),
            products_str,
            start_date.strftime('%Y-%m-%d %H:%M:%S'),
            end_date.strftime('%Y-%m-%d %H:%M:%S'),
            products_str,
        )
        self.env.cr.execute(OPENING_QUERY, (date_from, date_from, tuple(product_ids.ids)))
        products_opening_qty = self.env.cr.dictfetchall()

        self.env.cr.execute(OPENING_QUERY, (day_after_date_to, day_after_date_to, tuple(product_ids.ids)))
        products_closing_qty = self.env.cr.dictfetchall()

        self.env.cr.execute(VALUATION_AMT_QUERY, (date_from, tuple(product_ids.ids)))
        products_opening_amt = self.env.cr.dictfetchall()

        self.env.cr.execute(VALUATION_AMT_QUERY, (day_after_date_to, tuple(product_ids.ids)))
        products_closing_amt = self.env.cr.dictfetchall()

        _logger.info(f'\n{query}\n')
        self.env.cr.execute(query)
        result = self.env.cr.dictfetchall()
        product_ids = data.get('product_ids')
        transaction_product = []
        quantity = 0
        unit_cost = 0
        packaging_quantity = 0
        packaging_unit_cost =0
        for rec in result:
            product_id = rec.get('product_id')
            unpackaging_product = self.env['stock.repackaging.line'].search(
                [('product_id', '=', product_id), ('repackaging_id.state', '=', 'done'), ('repackaging_id.date', '>=', start_date_raw),
                 ('repackaging_id.date', '<=', end_date_raw)])
            if unpackaging_product:
                quantity = sum(unpackaging_product.filtered(lambda m: m.product_id.id == product_id).mapped("quantity"))
                unit_cost = sum(unpackaging_product.filtered(lambda l: l.product_id.id == product_id).mapped('unit_cost'))


            packaging_product = self.env['stock.packaging.line'].search(
                [('product_id', '=', product_id), ('stock_package_id.state', '=', 'done'), ('stock_package_id.date', '>=', start_date_raw),
                 ('stock_package_id.date', '<=', end_date_raw)])

            if packaging_product:
                packaging_quantity = sum(packaging_product.filtered(lambda m: m.product_id.id == product_id).mapped("qty"))
                packaging_unit_cost = sum(packaging_product.filtered(lambda l: l.product_id.id == product_id).mapped('unit_cost'))
            transaction_product.append(
                rec.get('product_id')
            )
            product = self.env['product.product'].browse(rec['product_id'])
            item_id = product.default_code
            item_description = product.name

            opening_rec = list(filter(lambda record: record['product_id'] == product.id,
                                      products_opening_qty))
            closing_rec = list(filter(lambda record: record['product_id'] == product.id,
                                      products_closing_qty))
            opening_amt_rec = list(filter(lambda record: record['product_id'] == product.id,
                                          products_opening_amt))
            closing_amt_rec = list(filter(lambda record: record['product_id'] == product.id,
                                          products_closing_amt))
            opening_qty = opening_rec[0]['qty'] if opening_rec else 0
            closing_qty = closing_rec[0]['qty'] if closing_rec else 0
            opening_amt = opening_amt_rec[0]['amt'] if opening_amt_rec else 0
            closing_amt = closing_amt_rec[0]['amt'] if closing_amt_rec else 0
            #
            # opening_amt = 0
            # closing_amt = 0

            purchase_qty = rec['purchase_qty'] or 0
            purchase_amt = rec['purchase_amt'] or 0
            purchase_return_qty = rec['purchase_return_qty'] or 0
            purchase_return_amt = rec['purchase_return_amt'] or 0
            sale_qty = rec['sale_qty'] or 0
            sale_amt = rec['sale_amt'] or 0
            sale_return_qty = rec['sale_return_qty'] or 0
            sale_return_amt = rec['sale_return_amt'] or 0
            pos_qty = rec['pos_qty'] or 0
            pos_amt = rec['pos_amt'] or 0
            pos_return_qty = rec['pos_return_qty'] or 0
            pos_return_amt = rec['pos_return_amt'] or 0
            production_qty = rec['production_qty'] or 0
            production_amt = rec['production_amt'] or 0
            unbuild_qty = rec['unbuild_qty'] or 0
            unbuild_amt = rec['unbuild_amt'] or 0
            scrap_qty = rec['scrap_qty'] or 0
            scrap_amt = rec['scrap_amt'] or 0
            adjustment_qty = rec['adjustment_qty'] or 0
            adjustment_amt = rec['adjustment_amt'] or 0
            # closing_qty = opening_qty + purchase_qty + purchase_return_qty + sale_qty + sale_return_qty + production_qty + unbuild_qty + scrap_qty + adjustment_qty
            # closing_amt = opening_amt + purchase_amt + purchase_return_amt + sale_amt + sale_return_amt + production_amt + unbuild_amt + scrap_amt + adjustment_amt

            records.append({
                'product_id': product,
                'opening_qty': opening_qty,
                'opening_amt': opening_amt,
                'purchase_qty': purchase_qty,
                'purchase_amt': purchase_amt,
                'purchase_return_qty': purchase_return_qty,
                'purchase_return_amt': purchase_return_amt,
                'sale_qty': sale_qty,
                'sale_amt': sale_amt,
                'sale_return_qty': sale_return_qty,
                'sale_return_amt': sale_return_amt,
                'pos_qty': pos_qty,
                'pos_amt': pos_amt,
                'pos_return_qty': pos_return_qty,
                'pos_return_amt': pos_return_amt,
                'production_qty': production_qty,
                'production_amt': production_amt,
                'unbuild_qty': unbuild_qty,
                'unbuild_amt': unbuild_amt,
                'scrap_qty': scrap_qty,
                'scrap_amt': scrap_amt,
                'adjustment_qty': adjustment_qty,
                'adjustment_amt': adjustment_amt,
                'unpackaging_qty': quantity or 0.00,
                'unpackaging_cost': unit_cost or 0.00,
                'packaging_qty':packaging_quantity or 0.0,
                'packaging_unit_cost':packaging_unit_cost or 0.0,
                'closing_qty': closing_qty,
                'closing_amt': closing_amt,
                'no_transaction': False,
            })

        no_transaction_products = set(product_ids) - set(transaction_product)

        # for product in no_transaction_products:
        #     product = self.env['product.product'].browse(product)
        #
        #     opening_rec = list(filter(lambda record: record['product_id'] == product.id,
        #                               products_opening_qty))
        #     closing_rec = list(filter(lambda record: record['product_id'] == product.id,
        #                               products_closing_qty))
        #     opening_amt_rec = list(filter(lambda record: record['product_id'] == product.id,
        #                                   products_opening_amt))
        #     closing_amt_rec = list(filter(lambda record: record['product_id'] == product.id,
        #                                   products_closing_amt))
        #     opening_qty = opening_rec[0]['qty'] if opening_rec else 0.0
        #     closing_qty = closing_rec[0]['qty'] if closing_rec else 0.0
        #     opening_amt = opening_amt_rec[0]['amt'] if opening_amt_rec else 0
        #     closing_amt = closing_amt_rec[0]['amt'] if closing_amt_rec else 0
        #
        #     # opening_amt = 0
        #     # closing_amt = 0
        #
        #     records.append({
        #         'product_id': product,
        #         'opening_qty': opening_qty,
        #         'opening_amt': opening_amt,
        #         'purchase_qty': 0,
        #         'purchase_amt': 0,
        #         'purchase_return_qty': 0,
        #         'purchase_return_amt': 0,
        #         'sale_qty': 0,
        #         'sale_amt': 0,
        #         'sale_return_qty': 0,
        #         'sale_return_amt': 0,
        #         'pos_qty': 0,
        #         'pos_amt': 0,
        #         'pos_return_qty': 0,
        #         'pos_return_amt': 0,
        #         'production_qty': 0,
        #         'production_amt': 0,
        #         'unbuild_qty': 0,
        #         'unbuild_amt': 0,
        #         'scrap_qty': 0,
        #         'scrap_amt': 0,
        #         'adjustment_qty': 0,
        #         'adjustment_amt': 0,
        #         'closing_qty': closing_qty,
        #         'closing_amt': closing_amt,
        #         'no_transaction': True,
        #     })

        if records:
            self.group_by_products(workbook, sheet, records, start_date)

    def group_by_products(self, workbook, sheet, grouped_records, start_date):
        row_index = 7
        total_opening_qty = total_opening_amt = total_closing_qty = total_closing_amt = 0
        total_purchase_qty = total_purchase_amt = total_purchase_return_qty = 0
        total_purchase_return_amt = total_sale_qty = total_sale_amt = 0
        total_sale_return_qty = total_sale_return_amt = 0
        total_adj_qty = total_adj_amt = total_production_qty = total_production_amt = 0
        total_scrap_qty = total_scrap_amt = 0
        total_unbuild_qty = total_unbuild_amt = total_update_cost_amt = 0
        total_pos_qty = 0
        total_pos_amt = 0
        total_pos_return_qty = 0
        total_pos_return_amt = 0

        cell_center = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9, 'valign': 'vcenter', 'align': 'center', 'border': 1,'num_format': '#,##0.00',
        })
        cell_left = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9, 'valign': 'vcenter', 'align': 'left', 'border': 1,'num_format': '#,##0.00',
        })
        cell_right = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9, 'valign': 'vcenter', 'align': 'right', 'border': 1,'num_format': '#,##0.00',
        })
        footer_cell_center = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9, 'valign': 'vcenter', 'bold': True, 'align': 'center', 'border': 1,'num_format': '#,##0.00',
        })
        footer_cell_right = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9, 'valign': 'vcenter', 'bold': True, 'align': 'right', 'border': 1,'num_format': '#,##0.00',
        })

        for record in grouped_records:
            number = 1
            product = self.env['product.product'].browse(record['product_id'].id)
            template = self.env['product.product'].browse(record['product_id'].id).product_tmpl_id

            opening_qty = record['opening_qty']
            opening_amt = record['opening_amt']
            purchase_qty = record['purchase_qty']
            purchase_amt = record['purchase_amt']
            purchase_return_qty = record['purchase_return_qty']
            purchase_return_amt = record['purchase_return_amt']
            sale_qty = record['sale_qty']
            sale_amt = record['sale_amt']
            sale_return_qty = record['sale_return_qty']
            sale_return_amt = record['sale_return_amt']
            pos_qty = record['pos_qty']
            pos_amt = record['pos_amt']
            pos_return_qty = record['pos_return_qty']
            pos_return_amt = record['pos_return_amt']
            production_qty = record['production_qty']
            production_amt = record['production_amt']
            unbuild_qty = record['unbuild_qty']
            unbuild_amt = record['unbuild_amt']
            scrap_qty = record['scrap_qty']
            scrap_amt = record['scrap_amt']
            adjustment_qty = record['adjustment_qty']
            adjustment_amt = record['adjustment_amt']
            closing_qty = record['closing_qty']
            closing_amt = record['closing_amt']
            quantity = record['unpackaging_qty']
            unit_cost = record['unpackaging_cost']
            packaging_qty = record['packaging_qty']
            packaging_unit_cost = record['packaging_unit_cost']

            if closing_qty != 0.0:
                total_opening_qty += opening_qty
                total_opening_amt += opening_amt
                total_closing_qty += closing_qty
                total_closing_amt += closing_amt
                total_purchase_qty += purchase_qty
                total_purchase_amt += purchase_amt
                total_purchase_return_qty += purchase_return_qty
                total_purchase_return_amt += purchase_return_amt
                total_sale_qty += sale_qty
                total_sale_amt += sale_amt
                total_sale_return_qty += sale_return_qty
                total_sale_return_amt += sale_return_amt
                total_pos_qty += pos_qty
                total_pos_amt += pos_amt
                total_pos_return_qty += pos_return_qty
                total_pos_return_amt += pos_return_amt
                total_adj_qty += adjustment_qty
                total_adj_amt += adjustment_amt
                total_production_qty += production_qty
                total_production_amt += production_amt
                total_unbuild_qty += unbuild_qty
                total_unbuild_amt += unbuild_amt
                total_scrap_qty += scrap_qty
                total_scrap_amt += scrap_amt

                sheet.write(f'A{row_index}', product.default_code or '', cell_center)
                sheet.write(f'B{row_index}', product.name, cell_left)

                sheet.write(f'C{row_index}', opening_qty, cell_right)
                sheet.write(f'D{row_index}', product.uom_id.name, cell_center)
                sheet.write(f'E{row_index}', opening_amt, cell_right)

                sheet.write(f'F{row_index}', purchase_qty, cell_right)
                sheet.write(f'G{row_index}', product.uom_id.name, cell_center)
                sheet.write(f'H{row_index}',purchase_amt, cell_right)

                sheet.write(f'I{row_index}', purchase_return_qty, cell_right)
                sheet.write(f'J{row_index}', product.uom_id.name, cell_center)
                sheet.write(f'K{row_index}', purchase_return_amt, cell_right)

                sheet.write(f'L{row_index}', sale_qty, cell_right)
                sheet.write(f'M{row_index}', product.uom_id.name, cell_center)
                sheet.write(f'N{row_index}',sale_amt, cell_right)

                sheet.write(f'O{row_index}', sale_return_qty, cell_right)
                sheet.write(f'P{row_index}', product.uom_id.name, cell_center)
                sheet.write(f'Q{row_index}', sale_return_amt, cell_right)

                sheet.write(f'R{row_index}', pos_qty, cell_right)
                sheet.write(f'S{row_index}', product.uom_id.name, cell_center)
                sheet.write(f'T{row_index}',pos_amt, cell_right)

                sheet.write(f'U{row_index}', pos_return_qty, cell_right)
                sheet.write(f'V{row_index}', product.uom_id.name, cell_center)
                sheet.write(f'W{row_index}', pos_return_amt, cell_right)

                sheet.write(f'X{row_index}', production_qty, cell_right)
                sheet.write(f'Y{row_index}', product.uom_id.name, cell_center)
                sheet.write(f'Z{row_index}',production_amt, cell_right)

                sheet.write(f'AA{row_index}', unbuild_qty, cell_right)
                sheet.write(f'AB{row_index}', product.uom_id.name, cell_center)
                sheet.write(f'AC{row_index}', unbuild_amt, cell_right)

                sheet.write(f'AD{row_index}', adjustment_qty, cell_right)
                sheet.write(f'AE{row_index}', product.uom_id.name, cell_center)
                sheet.write(f'AF{row_index}',adjustment_amt, cell_right)

                sheet.write(f'AG{row_index}', scrap_qty, cell_right)
                sheet.write(f'AH{row_index}', product.uom_id.name, cell_center)
                sheet.write(f'AI{row_index}',scrap_amt, cell_right)

                sheet.write(f'AJ{row_index}', packaging_qty, cell_right)
                sheet.write(f'AK{row_index}', product.uom_id.name, cell_center)
                sheet.write(f'AL{row_index}', packaging_unit_cost, cell_right)

                sheet.write(f'AM{row_index}',quantity, cell_right)
                sheet.write(f'AN{row_index}', product.uom_id.name, cell_center)
                sheet.write(f'AO{row_index}',unit_cost, cell_right)

                sheet.write(f'AP{row_index}', closing_qty, cell_right)
                sheet.write(f'AQ{row_index}', product.uom_id.name, cell_center)
                sheet.write(f'AR{row_index}', closing_amt, cell_right)

                row_index += 1
                number += 1

        sheet.write(f'A{row_index}', '')
        sheet.write(f'B{row_index}', 'Total', footer_cell_center)

        sheet.write(f'C{row_index}', total_opening_qty, footer_cell_right)
        sheet.write(f'D{row_index}', '', footer_cell_center)
        sheet.write(f'E{row_index}', total_opening_amt, footer_cell_right)

        sheet.write(f'F{row_index}', total_purchase_qty, footer_cell_right)
        sheet.write(f'G{row_index}', '', footer_cell_center)
        sheet.write(f'H{row_index}', total_purchase_amt, footer_cell_right)

        sheet.write(f'I{row_index}', total_purchase_return_qty, footer_cell_right)
        sheet.write(f'J{row_index}', '', footer_cell_center)
        sheet.write(f'K{row_index}', total_purchase_return_amt, footer_cell_right)

        sheet.write(f'L{row_index}', total_sale_qty, footer_cell_right)
        sheet.write(f'M{row_index}', '', footer_cell_center)
        sheet.write(f'N{row_index}', total_sale_amt, footer_cell_right)

        sheet.write(f'O{row_index}', total_sale_return_qty, footer_cell_right)
        sheet.write(f'P{row_index}', '', footer_cell_center)
        sheet.write(f'Q{row_index}', total_sale_return_amt, footer_cell_right)

        sheet.write(f'R{row_index}', total_pos_qty, footer_cell_right)
        sheet.write(f'S{row_index}', '', footer_cell_center)
        sheet.write(f'T{row_index}', total_pos_amt, footer_cell_right)

        sheet.write(f'U{row_index}', total_pos_return_qty, footer_cell_right)
        sheet.write(f'V{row_index}', '', footer_cell_center)
        sheet.write(f'W{row_index}', total_pos_return_amt, footer_cell_right)

        sheet.write(f'X{row_index}', total_production_qty, footer_cell_right)
        sheet.write(f'Y{row_index}', '', footer_cell_center)
        sheet.write(f'Z{row_index}', total_production_amt, footer_cell_right)

        sheet.write(f'AA{row_index}', total_unbuild_qty, footer_cell_right)
        sheet.write(f'AB{row_index}', '', footer_cell_center)
        sheet.write(f'AC{row_index}', total_unbuild_amt, footer_cell_right)

        sheet.write(f'AD{row_index}', total_adj_qty, footer_cell_right)
        sheet.write(f'AE{row_index}', '', footer_cell_center)
        sheet.write(f'AF{row_index}', total_adj_amt, footer_cell_right)

        sheet.write(f'AG{row_index}', total_scrap_qty, footer_cell_right)
        sheet.write(f'AH{row_index}', '', footer_cell_center)
        sheet.write(f'AI{row_index}', total_scrap_amt, footer_cell_right)

        sheet.write(f'AJ{row_index}', 0.00, footer_cell_right)
        sheet.write(f'AK{row_index}', '', footer_cell_center)
        sheet.write(f'AL{row_index}', 0.00, footer_cell_right)

        sheet.write(f'AM{row_index}', 0.00, footer_cell_right)
        sheet.write(f'AN{row_index}', '', footer_cell_center)
        sheet.write(f'AO{row_index}', 0.00, footer_cell_right)

        sheet.write(f'AP{row_index}', total_closing_qty, footer_cell_right)
        sheet.write(f'AQ{row_index}', '', footer_cell_center)
        sheet.write(f'AR{row_index}', total_closing_amt, footer_cell_right)


class InventoryActivitiesCostReport(models.TransientModel):
    _name = 'inventory.activities.cost.reports'
    _description = 'Inventory Activities With Cost Reports'
    _rec_name = 'start_date'

    start_date = fields.Date('Start Date', required=1,
                             default=lambda self: fields.Date.context_today(self) + relativedelta(day=1))
    end_date = fields.Date('End Date', required=1,
                           default=lambda self: fields.Date.context_today(self) + relativedelta(day=31))
    product_ids = fields.Many2many('product.product', domain=[('detailed_type', '=', 'product')], string='Products')

    def btn_print(self):
        products = self.product_ids
        if not products:
            products = self.env['product.product'].with_context(active_test=False).search(
                [('detailed_type', '=', 'product')])
        return self.env.ref('inventory_activities_reports.action_inventory_activities_cost_reports_xlsx').report_action(
            self,
            data={
                'start_date': self.start_date,
                'end_date': self.end_date,
                'product_ids': products.ids,
            })
