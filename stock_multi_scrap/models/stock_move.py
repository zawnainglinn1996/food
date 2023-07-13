from odoo import api, models, fields, _


class StockMove(models.Model):

    _inherit = 'stock.move'

    multi_scrap_analytic_acc_id = fields.Many2one('account.analytic.account', 'Multi Scrap Analytic Account')

    def _prepare_account_move_vals(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost):
        values = super(StockMove, self)._prepare_account_move_vals(credit_account_id,
                                                                   debit_account_id,
                                                                   journal_id,
                                                                   qty,
                                                                   description,
                                                                   svl_id,
                                                                   cost)
        values.update({'analytic_account_id': self.multi_scrap_analytic_acc_id.id})
        return values
