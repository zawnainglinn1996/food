from odoo import models, fields, api, _

class DocumentCheckList(models.Model):
    _name = "document.checklist"
    _description = "Document Checklist"

    name = fields.Char("Required Documents")
    register_no = fields.Char(string='Register No')
    date = fields.Date("Validation Date")
    attachment = fields.Binary(string="Attachment",attachment=True)
    file_name = fields.Char('Name')
    remark = fields.Text("Remarks")

    partner_id = fields.Many2one('res.partner', string='Partner Reference', required=True, ondelete='cascade', index=True, copy=False)