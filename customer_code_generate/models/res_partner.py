from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError, ValidationError


class Partner(models.Model):
    _inherit = "res.partner"

    customer_code = fields.Char("Customer Code", readonly=True, copy=False, store=True, index=True, tracking=True)
    company_code = fields.Char('Company Code')

    @api.onchange('company_id')
    def onchange_company_id(self):
        if self.company_id:
            self.company_code = self.company_id.short_code

    def generate_customer_sequence_code(self):
        already_exists = [r.name for r in self if r.customer and r.customer_code]
        if already_exists:
            raise ValidationError(
                'The following Customers have already been assigned Customer codes.\n' + '\n'.join(already_exists))
        for rec in self:
            if rec.name and rec.customer:
                partner_name = rec.name
                sequence_code = partner_name[0].upper()
                if not rec.ref and not rec.customer_code:
                    rec.ref = self.env['ir.sequence'].next_by_code(f'customer.{sequence_code.lower()}.sequence')
                    rec.customer_code = rec.ref
