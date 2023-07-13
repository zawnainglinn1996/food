from odoo import fields, models, api,_
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    backdate = fields.Datetime(string='Back Date', readonly=True, required=True,
                               states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                               default=fields.Datetime.now)

    @api.onchange('backdate')
    def onchange_backdate(self):
        if self.backdate:
            self.date_order = self.backdate

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        self.picking_ids.write({'scheduled_date': self.backdate})
        return res

    def _prepare_confirmation_values(self):
        return {
            'state': 'sale',
            'date_order': self.backdate,
            'commitment_date': self.backdate,
        }

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        self.picking_ids.write({
            'scheduled_date': self.backdate
        })
        return res

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        res.update({
            'invoice_date': self.date_order,
            'date': self.date_order,
        })
        return res
