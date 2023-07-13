from odoo import api, models, fields
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime
from dateutil.relativedelta import relativedelta


# class SaleOrderReport(models.AbstractModel):
#
#     _name = 'report.report_form.sale_quotation_report'
#
#     @api.model
#     def _get_report_values(self, docids, data=None):
#         objects = self.env['sale.order'].search([])
#         return objects
