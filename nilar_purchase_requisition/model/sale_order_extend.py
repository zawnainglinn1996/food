from odoo import models, fields, api, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_used_picking = fields.Boolean(string='Used Picking', default=False)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # THIS IS PICKING NUMBER CARRYING TO INVOICE FORM ZNL
    def _prepare_invoice(self):
        self.ensure_one()
        values = super(SaleOrder, self)._prepare_invoice()
        pickings = self.picking_ids.filtered(
            lambda p: p.picking_type_id.code == 'outgoing' and p.state == 'done' and p.is_used_picking == False)
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
        values.update({

            'picking_number': picking.name,

        })
        return values
