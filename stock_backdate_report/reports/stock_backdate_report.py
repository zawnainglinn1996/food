from odoo import models, fields


class StockBackdateReport(models.Model):

    _name = 'stock.backdate.report'
    _description = 'Stock Backdate Report'
    _auto = False
    _rec_name = 'product_id'

    default_code = fields.Char('Internal Reference')
    product_id = fields.Many2one('product.product', 'Product')
    location_id = fields.Many2one('stock.location', 'Location')
    on_hand_qty = fields.Float('On Hand')
    uom_id = fields.Many2one('uom.uom', 'UoM')

    @property
    def _table_query(self):
        date = self.env.context.get('inventory_date', fields.Datetime.now())
        query = f"""
        SELECT      ROW_NUMBER() OVER(ORDER BY PRODUCT_ID, LOCATION_ID) AS ID, 
                    PRODUCT_ID, 
                    DEFAULT_CODE, 
                    LOCATION_ID, 
                    SUM(ON_HAND_QTY) AS ON_HAND_QTY, 
                    UOM_ID    
        FROM 
        (
        SELECT      SML.PRODUCT_ID,
                    PT.DEFAULT_CODE,
                    SML.LOCATION_ID,
                    SUM(
                        -SML.QTY_DONE / NULLIF(COALESCE(LINE_UOM.FACTOR, 1) / COALESCE(PRODUCT_UOM.FACTOR, 1), 0.0)
                    ) AS ON_HAND_QTY,
                    PT.UOM_ID AS UOM_ID
        FROM        STOCK_MOVE_LINE SML
                    LEFT JOIN STOCK_MOVE SM ON SM.ID=SML.MOVE_ID
                    LEFT JOIN PRODUCT_PRODUCT PP ON PP.ID=SML.PRODUCT_ID
                    LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID=PP.PRODUCT_TMPL_ID
                    LEFT JOIN STOCK_LOCATION SL ON SL.ID=SML.LOCATION_ID
                    LEFT JOIN UOM_UOM PRODUCT_UOM ON PRODUCT_UOM.ID=PT.UOM_ID
                    LEFT JOIN UOM_UOM LINE_UOM ON LINE_UOM.ID=SML.PRODUCT_UOM_ID
        WHERE       SML.DATE <= '{date}' AND SL.USAGE='internal' 
        GROUP BY    SML.ID, SML.PRODUCT_ID, PT.DEFAULT_CODE, SML.LOCATION_ID, PT.UOM_ID
        
        UNION ALL
        
        SELECT      SML.PRODUCT_ID,
                    PT.DEFAULT_CODE,
                    SML.LOCATION_DEST_ID AS LOCATION_ID,
                    SUM(
                        SML.QTY_DONE / NULLIF(COALESCE(LINE_UOM.FACTOR, 1) / COALESCE(PRODUCT_UOM.FACTOR, 1), 0.0)
                    ) AS ON_HAND_QTY,
                    PT.UOM_ID AS UOM_ID
        FROM        STOCK_MOVE_LINE SML
                    LEFT JOIN STOCK_MOVE SM ON SM.ID=SML.MOVE_ID
                    LEFT JOIN PRODUCT_PRODUCT PP ON PP.ID=SML.PRODUCT_ID
                    LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID=PP.PRODUCT_TMPL_ID
                    LEFT JOIN STOCK_LOCATION DL ON DL.ID=SML.LOCATION_DEST_ID
                    LEFT JOIN UOM_UOM PRODUCT_UOM ON PRODUCT_UOM.ID=PT.UOM_ID
                    LEFT JOIN UOM_UOM LINE_UOM ON LINE_UOM.ID=SML.PRODUCT_UOM_ID
        WHERE       SML.DATE <= '{date}' AND DL.USAGE='internal' 
        GROUP BY    SML.ID, SML.PRODUCT_ID, PT.DEFAULT_CODE, SML.LOCATION_DEST_ID, PT.UOM_ID
        ) AS STOCK_BACKDATE_REPORT  
        
        GROUP BY    PRODUCT_ID, DEFAULT_CODE, LOCATION_ID, UOM_ID      
        """
        return query
