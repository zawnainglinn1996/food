from odoo import api, models, fields, _
from datetime import datetime


class PosConfig(models.Model):
    _inherit = 'pos.config'

    logo = fields.Image('Logo')


class PosOrder(models.Model):
    _inherit = 'pos.order'

    table_no = fields.Char(string='Table No')

    def _compute_order_name(self):
        if len(self.refunded_order_ids) != 0:
            return ','.join(self.refunded_order_ids.mapped('name')) + _(' REFUND')
        else:
            current_month = datetime.now().strftime('%h')
            current_year = datetime.now().strftime('%Y')
            counter_name = self.session_id.config_id.name
            year_and_month = str(current_year) + '/' + str(current_month) + '/'
            seq = self.env['ir.sequence'].next_by_code('nilar.pos')
            seq_data = counter_name + '/' + year_and_month + seq
            return seq_data
