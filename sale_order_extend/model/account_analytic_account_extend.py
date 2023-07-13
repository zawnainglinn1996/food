from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    short_code = fields.Char(string='Short Code')
    location_id = fields.Many2one('stock.location', string='Warehouse')

    @api.constrains('location_id')
    def check_contact_name(self):
        for rec in self:
            analytics = self.env['account.analytic.account'].search(
                [('location_id', '=', rec.location_id.id), ('id', '!=', rec.id)])
            if analytics:
                raise ValidationError(_(" The Location (%s/%s) already Used." % ( rec.location_id.location_id.name,rec.location_id.name)))
