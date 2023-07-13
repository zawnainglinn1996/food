from typing import re

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError
from odoo.osv.expression import expression


class WholeSaleSummaryReport(models.Model):
    _name = 'whole.sale.summary.report'
    _auto = False
    _description = 'Whole Sale Summary Report'
    _rec_name = 'order_date'
    _order = 'order_date desc'

    order_date = fields.Date(string='Order Date')
    partner_id = fields.Many2one('res.partner', string='Customer Name')
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    phone_no = fields.Char(string='Phone')
    qty = fields.Float(string='Quantity')
    uom_id = fields.Many2one('uom.uom', 'UOM', required=True)
    remark = fields.Char(string='Remark')
    expected_datetime = fields.Datetime(string='Expected Datetime')

    to_shop_name = fields.Many2one('shop.to.take', string='ယူမည့်ဆိုင်')
    state = fields.Selection([
        ('draft', 'Draft Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Sales Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    order_id = fields.Many2one('sale.order', 'Order #', readonly=True)
    avg_days_to_confirm = fields.Float(
        'Average Days To Confirm', readonly=True, store=False,)
    def _select_sale(self, fields=None):
        if not fields:
            fields = {}
        select_ = """
            coalesce(min(wsrl.id)) as id,
            wsrl.product_id as product_id,
            wsrl.allowed_qty as qty,
            wsrl.product_uom_id as uom_id,
            wsrl.remark as remark,
            (s.date_order + interval '6:30') as order_date,
            s.state as state,
            (wsr.scheduled_date)  as expected_datetime,
            s.analytic_account_id as analytic_account_id,
            s.partner_id as partner_id,
            partner.phone as phone_no,   
            s.to_shop_name as to_shop_name,
            s.id as order_id  
        """
        for field in fields.values():
            select_ += field
        return select_

    def _from_sale(self, from_clause=''):
        from_ = """
                whole_sale_requisition_line wsrl
                      join whole_sale_requisition wsr on (wsrl.requisition_id = wsr.id)
                        left join product_product p on (wsrl.product_id=p.id)
                            left join product_template t on (p.product_tmpl_id=t.id)
                        left join sale_order s on (wsr.sale_order_id = s.id)
                        left join res_partner partner on s.partner_id = partner.id
                
        """.format(
            currency_table=self.env['res.currency']._get_query_currency_table(
                {'multi_company': True, 'date': {'date_to': fields.Date.today()}}),
        )
        return from_

    def where_by_sale(self, where_=''):
        where_ = """
                    wsrl.display_type IS NULL 
                    AND t.detailed_type = 'product'
                    AND s.state != 'cancel'
                    %s
                """ % where_
        return where_

    def _group_by_sale(self, groupby=''):
        groupby_ = """
            wsrl.product_id,
            wsrl.allowed_qty,
            wsr.scheduled_date,
            wsrl.product_uom_id,
            wsrl.remark,
            s.date_order,
            s.state,
            s.analytic_account_id,
            s.partner_id,
            partner.phone, 
            s.to_shop_name,  
            s.id
        """
        return groupby_

    def _query(self, with_clause='', fields=None, groupby='', from_clause='', where_=''):
        if not fields:
            fields = {}
        with_ = ("WITH %s" % with_clause) if with_clause else ""
        return '%s (SELECT %s FROM %s WHERE %s GROUP BY %s)' % \
               (with_, self._select_sale(fields), self._from_sale(from_clause), self.where_by_sale(where_), self._group_by_sale(groupby))

    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))
