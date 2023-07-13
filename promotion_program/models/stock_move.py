from odoo import api, models, fields


class StockMove(models.Model):

    _inherit = 'stock.move'

    promotion_account_id = fields.Many2one('account.account', 'Promotion COA')

    def _action_confirm(self, merge=True, merge_into=False):
        merge = merge_into = False
        return super()._action_confirm(merge, merge_into)
