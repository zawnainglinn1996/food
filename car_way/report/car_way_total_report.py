import logging
from odoo import models, fields, api, _, tools
_logger = logging.getLogger(__name__)

class WholeRetailSummaryReport(models.Model):
    _name = 'car.way.total.report'
    _description = 'Car Way Total Report'
    _rec_name = 'car_way_id'
    _auto = False

    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    qty = fields.Float(string='Qty', default=0.0)
    uom_id = fields.Many2one('uom.uom', 'UOM', required=False)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    product_packaging_id = fields.Many2one('product.packaging', string='Packaging')
    packaging_size = fields.Float(string='Packaging Size')
    sale_type = fields.Selection([
        ('whole_sale', 'Whole Sale'),
        ('retail_sale', 'Retail Sale'),
    ], string='Sale Type', readonly=True)
    sale_picking = fields.Selection([
        ('delivery', 'Delivery'),
        ('pickup', 'Pickup'),
    ], string='Picking Type', readonly=True)
    expected_date = fields.Date(string='Expected Date')
    remark = fields.Char(string='Remark')

    car_way_id = fields.Many2one('car.way.name', string='Car Way Name')
    car_number = fields.Char(string='Car Number')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = """ 
            SELECT
                  DISTINCT SM.ID,
                  SM.PRODUCT_QTY AS QTY,
                  SM.PRODUCT_ID,
                  SM.PRODUCT_UOM AS UOM_ID,
                  SM.PRODUCT_PACKAGING_ID,
                  DATE(SP.SCHEDULED_DATE + INTERVAL '6 hours 30 minutes') AS EXPECTED_DATE,
                  SP.ANALYTIC_ACCOUNT_ID,
                  WSR.SALE_TYPE,
                  SP.CAR_WAY_ID,
                  CWL.CAR_NAME AS CAR_NUMBER,
                  SM.REMARK,
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
                  AND  SP.IS_ASSIGNED = TRUE"""
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, query))
