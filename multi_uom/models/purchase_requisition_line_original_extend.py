from odoo import api, models, fields


class PurchaseRequisitionLine(models.Model):

    _inherit = "purchase.requisition.line"

    multi_uom_line_id = fields.Many2one('multi.uom.line', 'UoM')



