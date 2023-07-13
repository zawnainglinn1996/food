from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

class ResUser(models.Model):
    _inherit = "res.users"

    sale_market_user = fields.Boolean('Sale and Marketing', default=False,
                                      help='Check this box to allow using this user to put sale and marketing.')

    @api.constrains('sale_market_user')
    def _check_sale_market_user(self):
        if self.sale_market_user:
            checked_bool = self.search([('id', '!=', self.id), ('sale_market_user', '=', True)])
            if checked_bool:
                raise ValidationError(
                    _("There's already one sale and marketing is checked. Reference : %s") % checked_bool[0].name)
