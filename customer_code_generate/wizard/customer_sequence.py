from odoo import api, models


class CustomerSequence(models.TransientModel):
    _name = 'generate.customer.sequence'
    _description = 'Generate Customer Sequence'

    def action_generate_sequence(self):
        active_ids = self._context.get('active_ids', [])
        partner_ids = self.env['res.partner'].browse(active_ids)
        partner_ids.generate_customer_sequence_code()
