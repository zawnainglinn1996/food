from odoo import api, fields, models
from odoo.tools import float_compare


class StockWarnInsufficientQtyMulti(models.AbstractModel):
    _name = 'stock.warn.insufficient.qty.multi'
    _description = 'Warn Insufficient Quantity Multi'

    product_id = fields.Many2one('product.product', 'Product', required=True)
    location_id = fields.Many2one('stock.location', 'Location', domain="[('usage', '=', 'internal')]", required=True)
    quant_ids = fields.Many2many('stock.quant', compute='_compute_quant_ids')

    @api.depends('product_id')
    def _compute_quant_ids(self):
        self.quant_ids = self.env['stock.quant'].search([
            ('product_id', '=', self.product_id.id),
            ('location_id.usage', '=', 'internal')
        ])

    def action_done(self):
        raise NotImplementedError()


class StockWarnInsufficientQtyScrapMulti(models.TransientModel):
    _name = 'stock.warn.insufficient.qty.scrap.multi'
    _inherit = 'stock.warn.insufficient.qty.multi'
    _description = 'Warn Insufficient Scrap Quantity Multi'

    multi_scrap_id = fields.Many2one('stock.multi.scrap', 'Multi Scrap')
    multi_line_id = fields.Many2one('multi.scrap.line', 'Multi Scrap Line')

    def action_done(self):
        return self.multi_scrap_id.do_scrap()

    def action_cancel(self):
        # FIXME in master: we should not have created the scrap in a first place
        return self.multi_scrap_id.sudo().unlink()

