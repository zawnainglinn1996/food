from odoo import models, fields, api, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # THIS IS PICKING NUMBER CARRYING TO BILL FORM ZNL
    def _prepare_invoice(self):
        self.ensure_one()
        res = super(PurchaseOrder, self)._prepare_invoice()
        pickings = self.picking_ids.filtered(
            lambda p: p.picking_type_id.code == 'incoming' and p.state == 'done' and p.is_used_picking == False)
        if pickings:
            if len(pickings) > 1:
                picking = pickings[0]
            else:
                picking = pickings[-1]
        else:
            picking = self.env['stock.picking']
        picking.write({
            'is_used_picking': True
        })
        res.update({
            'picking_number': picking.name,
        })
        return res
