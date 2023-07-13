from odoo import models, fields, api, _, tools


class WholeRetailSummaryReport(models.Model):
    _name = 'whole.retail.summary.report'
    _description = 'Requisition Summary( Whole + Retail )'
    _auto = False

    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    request_qty = fields.Float(string='Required Qty', default=0.0)
    allowed_qty = fields.Float(string='Allowed Qty', default=0.0)
    uom_id = fields.Many2one('uom.uom', 'UOM', required=False)
    uom_name = fields.Char(string='UOM NAME')
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
    expected_date = fields.Datetime(string='Expected Datetime')
    remark = fields.Char(string='Remark')

    product_category_id = fields.Many2one('product.category', string='Product Category')
    product_group_id = fields.Many2one('product.group', string='Product Group')
    product_family_id = fields.Many2one('product.family', string='Product Family')

    def _select_sale(self, fields=None):
        if not fields:
            fields = {}
        select_ = """
            ROW_NUMBER () OVER (ORDER BY wl.product_id) AS ID,
            wl.product_id as product_id,
            wl.product_uom_id as uom_id,
            u.name as uom_name,
            SUM(wl.required_qty) as request_qty,
            SUM(wl.allowed_qty) as allowed_qty,
            wsr.analytic_account_id as analytic_account_id,
            wsr.sale_type as sale_type,
            (wsr.scheduled_date) as expected_date,
            wsr.sale_picking as sale_picking,
            wl.remark as remark,
            wl.product_packaging_id as product_packaging_id,
            wl.packaging_size as packaging_size,
            p.product_family_id as product_family_id,
            p.product_group_id as product_group_id,
            t.categ_id as product_category_id
        """
        for field in fields.values():
            select_ += field
        return select_

    def _from_sale(self, from_clause=''):
        from_ = """
                whole_sale_requisition_line wl
                      right outer join whole_sale_requisition wsr on (wsr.id=wl.requisition_id )
                      left join product_product p on (wl.product_id=p.id)
                      left join product_template t on (p.product_tmpl_id=t.id)
                      left join uom_uom u on (u.id=wl.product_uom_id)
                      left join uom_uom u2 on (u2.id=t.uom_id)
                      left join product_packaging pp on (pp.id=wl.product_packaging_id)
                      
        """.format(
            currency_table=self.env['res.currency']._get_query_currency_table(
                {'multi_company': True, 'date': {'date_to': fields.Date.today()}}),
        )
        return from_

    def _group_by_sale(self, groupby=''):
        groupby_ = """
            wl.product_id,
            wl.product_uom_id,
            wsr.analytic_account_id,
            wsr.sale_type,
            wsr.scheduled_date,
            wsr.sale_picking,
            wl.product_packaging_id,
            wl.remark,
            u.name,
            wl.packaging_size,
            t.categ_id,
            p.product_group_id,
            p.product_family_id
        """
        return groupby_

    def _query(self, with_clause='', fields=None, groupby='', from_clause=''):
        if not fields:
            fields = {}
        with_ = ("WITH %s" % with_clause) if with_clause else ""
        return "%s (SELECT %s FROM %s WHERE  wsr.state in ('approved', 'confirm') GROUP BY %s)" % \
               (with_, self._select_sale(fields), self._from_sale(from_clause), self._group_by_sale(groupby))

    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))
