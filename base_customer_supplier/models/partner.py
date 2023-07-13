from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Partner(models.Model):
    _inherit = "res.partner"

    customer = fields.Boolean(string='Is a Customer',
                              help="Check this box if this contact is a customer. It can be selected in sales orders.")
    supplier = fields.Boolean(string='Is a Vendor',
                              help="Check this box if this contact is a vendor. It can be selected in purchase orders.")

    contact_address = fields.Char(string='Address', compute='_get_contact_address')

    @api.depends('street', 'street2')
    def _get_contact_address(self):
        for rec in self:
            if rec.street or rec.street2:
                rec.contact_address = str(rec.street) or '' + ',' + str(rec.street2) or ''
            else:
                rec.contact_address = False

    @api.constrains('name')
    def check_contact_name(self):
        for rec in self:
            supplier_name = self.env['res.partner'].search([('name', '=', rec.name),
                                                             ('supplier', '=', True),
                                                             ('id', '!=', rec.id)])
            customer_name = self.env['res.partner'].search([('name', '=', rec.name),
                                                             ('customer', '=', True),
                                                             ('id', '!=', rec.id)])
            if supplier_name:
                raise ValidationError(_("Supplier(%s) already exists." % rec.name))
            elif customer_name:
                raise ValidationError(_("Customer(%s) already exists." % rec.name))
            else:
                pass

