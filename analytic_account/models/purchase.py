from odoo import api, models, fields, _ 
from odoo.exceptions import ValidationError
from odoo.http import request


class PurchaseOrder(models.Model):

    _inherit = 'purchase.order'

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    allow_analytic_account_ids = fields.Many2many('account.analytic.account', string='Analytic Accounts',
                                                  related='login_employee_id.allow_analytic_account_id')

    def _prepare_invoice(self):
        res = super(PurchaseOrder, self)._prepare_invoice()
        res.update({
            'analytic_account_id': self.analytic_account_id.id,
        })
        return res


class PurchaseOrderLine(models.Model):

    _inherit = 'purchase.order.line'

    @api.depends('product_id', 'date_order', 'order_id.analytic_account_id')
    def _compute_analytic_id_and_tag_ids(self):
        res = super(PurchaseOrderLine, self)._compute_analytic_id_and_tag_ids()
        for line in self:
            line.account_analytic_id = line.order_id.analytic_account_id.id
        return res