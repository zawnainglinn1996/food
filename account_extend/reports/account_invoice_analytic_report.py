from odoo import models, fields, api

from functools import lru_cache


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    amount_total = fields.Float('Subtotal', readonly=True)

    @api.model
    def _select(self):
        return super(AccountInvoiceReport, self)._select() + ", move.amount_total"
