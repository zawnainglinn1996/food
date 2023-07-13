import pytz
from datetime import datetime

from odoo import api, fields, models


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    date_expected = fields.Datetime('Expected Date', default=fields.Datetime.now)

    def do_scrap(self):
        self._check_company()
        for scrap in self:
            scrap.name = self.env['ir.sequence'].next_by_code('stock.scrap') or _('New')
            move = self.env['stock.move'].create(scrap._prepare_move_values())
            # master: replace context by cancel_backorder
            move.with_context(is_scrap=True, force_period_date=self.date_expected)._action_done()
            scrap.write({'move_id': move.id, 'state': 'done'})
            scrap.move_id.write({'date': self.date_expected})
            scrap.move_id.move_line_ids.write({'date': self.date_expected})
            scrap.date_done = self.date_expected
        return True


