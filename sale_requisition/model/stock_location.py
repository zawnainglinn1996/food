from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class Location(models.Model):
    _inherit = "stock.location"

    distribution_location = fields.Boolean('Is a Distribution  Location?', default=False,
                                           help='Check this box to allow using this location to put distribution.')

    @api.constrains('distribution_location')
    def _check_distribution_location(self):
        if self.distribution_location:
            checked_bool = self.search([('id', '!=', self.id), ('distribution_location', '=', True)])
            if checked_bool:
                raise ValidationError(
                    _("There's already one distribution location is checked. Reference : %s") % checked_bool[0].name)
