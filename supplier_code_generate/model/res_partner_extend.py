from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class Partner(models.Model):
    _inherit = "res.partner"

    supplier_code = fields.Char("Supplier Code", readonly=True, copy=False, store=True, index=True, tracking=True)

    @api.constrains('name')
    def check_name(self):
        for rec in self:
            partner_name = rec.name
            first_name = partner_name[0].upper()
            if first_name == ' ':
                raise ValidationError(_("Contact (%s) should not start with a space" % rec.name))

    def generate_sequence_code(self):
        already_exists = [r.name for r in self if r.supplier and r.supplier_code]
        if already_exists:
            raise ValidationError(
                'The following suppliers have already been assigned supplier codes.\n' + '\n'.join(already_exists))
        for rec in self:
            if rec.name and rec.supplier:
                partner_name = rec.name
                sequence_code = partner_name[0].upper()
                if not rec.ref and not rec.supplier_code:
                    rec.ref = self.env['ir.sequence'].next_by_code(f'supplier.{sequence_code.lower()}.sequence')
                    rec.supplier_code = rec.ref
