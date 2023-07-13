from odoo import api, models


class SupplierSequence(models.TransientModel):
    _name = 'generate.supplier.sequence'
    _description = "Generate Supplier Sequence"

    def action_generate_sequence(self):
        active_ids = self._context.get('active_ids', [])
        partner_ids = self.env['res.partner'].browse(active_ids)
        partner_ids.generate_sequence_code()
