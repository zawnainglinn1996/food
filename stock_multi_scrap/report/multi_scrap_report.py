from odoo import tools
from odoo import api, fields, models


class MultiScrapReport(models.Model):
    _name = "multi.scrap.report"
    _description = "Multi Scrap Report"
    _auto = False

    document_number = fields.Char(string='Document Number', readonly=True)
    date = fields.Datetime(string='Date', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    product_uom_id = fields.Many2one('uom.uom', 'Unit of Measure', readonly=True)
    location_id = fields.Many2one('stock.location', 'Source Location', readonly=True)
    scrap_location_id = fields.Many2one('stock.location', 'Scrap Location', readonly=True)
    scrap_qty = fields.Float('Scrap Quantity', default=1.0, readonly=True)
    standard_price = fields.Float('Cost', readonly=True)
    remark = fields.Char('Remark', readonly=True)
    multi_scrap_id = fields.Many2one('stock.multi.scrap', 'Scrap #', readonly=True)
    lot_id = fields.Many2one('stock.production.lot', 'Lot/Serial Number', readonly=True)
    picking_id = fields.Many2one('stock.picking', 'Picking', readonly=True)
    move_id = fields.Many2one('stock.move', 'Scrap Move', readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', readonly=True)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], string='Status', readonly=True)


    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        with_ = ("WITH %s" % with_clause) if with_clause else ""

        select_ = """
            min(msl.id) as id, 
            msl.product_id as product_id,
            msl.lot_id as lot_id,
            msl.scrap_qty as scrap_qty,
            msl.product_uom_id as product_uom_id,
            msl.location_id as location_id,
            msl.scrap_location_id as scrap_location_id,
            msl.remark as remark,
            msl.analytic_account_id as analytic_account_id,
            msl.picking_id as picking_id,
            msl.move_id as move_id,
            msl.cost as standard_price,
            sms.excepted_date as date,
            sms.document_number as document_number,
            sms.state as state,
            sms.id as multi_scrap_id
        """

        for field in fields.values():
            select_ += field

        from_ = """
                multi_scrap_line msl
                    join stock_multi_scrap sms on (msl.multi_scrap_id=sms.id)
                    left join product_product p on (msl.product_id=p.id)
                        left join product_template t on (p.product_tmpl_id=t.id)
                %s
        """ % from_clause

        groupby_ = """      
            msl.id,
            msl.product_id,
            msl.lot_id,
            msl.scrap_qty,
            msl.product_uom_id,
            msl.location_id,
            msl.scrap_location_id,
            msl.remark,
            msl.analytic_account_id,
            msl.picking_id,
            msl.move_id,
            msl.cost,
            sms.excepted_date,
            sms.document_number,
            sms.state,
            sms.id %s
        """ % (groupby)

        return '%s (SELECT %s FROM %s GROUP BY %s)' % (with_, select_, from_, groupby_)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))


