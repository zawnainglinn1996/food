from odoo import fields, models, api


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.onchange('date_order')
    def _onchange_date(self):
        if self.date_order:
            self.date_planned = self.date_order

    def button_approve(self, force=False):
        result = super(PurchaseOrder, self).button_approve(force=force)
        self.write({'state': 'purchase', 'date_approve': self.date_order})
        return result

    def _prepare_invoice(self):
        res = super(PurchaseOrder, self)._prepare_invoice()
        res.update({
            'invoice_date': self.effective_date,
            'date': self.effective_date,
        })
        return res