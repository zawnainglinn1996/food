from odoo import models, fields, api, _


class StockMove(models.Model):
    _inherit = 'stock.move'

    lot_id = fields.Many2one('stock.production.lot', domain="[('product_id', '=', product_id)]",
                             string='Batch Number')
    expiration_date = fields.Datetime(string='Expiration Date')

    @api.onchange('lot_id')
    def onchange_lot_id(self):
        for rec in self:
            if rec.lot_id:
                rec.expiration_date = rec.lot_id.expiration_date

    def _update_reserved_quantity(self, need, available_quantity, location_id, lot_id=None, package_id=None,
                                  owner_id=None, strict=True,
                                  ):
        # if self._context.get("serial"):
        if self.sale_line_id:
            lot_id = self.sale_line_id.lot_id
        return super()._update_reserved_quantity(
            need,
            available_quantity,
            location_id,
            lot_id=lot_id,
            package_id=package_id,
            owner_id=owner_id,
            strict=strict,
        )

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        values = super(StockMove, self)._prepare_move_line_vals(quantity, reserved_quant)
        if self.purchase_line_id:
            values['lot_id'] = self.lot_id.id
            values['lot_name'] = self.lot_id.name

        if reserved_quant and self.sale_line_id:
            values['lot_id'] = self.lot_id.id
        return values
