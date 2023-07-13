import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class FieldSecurity(models.Model):
    _name = 'generic.security.restriction.field'
    _description = 'Fields Security'

    model_id = fields.Many2one('ir.model', required=True, index=True, ondelete='cascade')
    field_id = fields.Many2one('ir.model.fields', required=True, index=True, ondelete='cascade')
    field_name = fields.Char(related='field_id.name', readonly=True)
    group_ids = fields.Many2many(
        'res.groups', 'fields_security_restriction_group_relation',
        'group_id', 'field_security_id', required=True, string='Groups')
    set_readonly = fields.Boolean(default=False)
    set_invisible = fields.Boolean(default=False)
    hide_stat_button = fields.Boolean(default=False)
