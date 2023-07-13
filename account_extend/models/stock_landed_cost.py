from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.http import request


class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    @api.model
    def default_get(self, fields_list):
        vals = super(StockLandedCost, self).default_get(fields_list)
        default_journal_id = False

        if request.session.emp_id:
            data = int(request.session.emp_id)
            employee_id = self.env['hr.employee'].search([('id', '=', data)])
            if employee_id:
                journal_id = self.env['ir.property']._get("property_stock_journal", "product.category")
                default_journal_id = journal_id
        if default_journal_id:
            vals.update({'account_journal_id': default_journal_id})
        return vals

    @api.onchange('account_journal_id')
    def onchange_journal(self):
        for rec in self:
            if request.session.emp_id:
                data = int(request.session.emp_id)
                employee_id = self.env['hr.employee'].search([('id', '=', data)])

                if employee_id:
                    return {'domain': {'account_journal_id': [('id', 'in', employee_id.journal_ids.ids)]}}

    def write(self, vals):

        res = super(StockLandedCost, self).write(vals)
        if self.account_journal_id:
            if request.session.emp_id:
                data = int(request.session.emp_id)
                employee_id = self.env['hr.employee'].search([('id', '=', data)])

                if employee_id:
                    journal_ids = employee_id.journal_ids.ids
                    if self.account_journal_id not in journal_ids:
                        raise ValidationError(
                            _("Journal Name -%s is not include allow journal access of  Employee - ( %s)!" % (
                            self.account_journal_id.name, employee_id.name)))

        return res
