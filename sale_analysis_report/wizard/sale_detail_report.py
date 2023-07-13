from odoo import api, models, fields, _


class SaleDetailReportWizard(models.TransientModel):
    _name = 'sale.detail.report'
    _description = 'Sale Detail Reports'

    date_from = fields.Date('Date From', required=True)
    date_to = fields.Date('Date To', required=True)
    analytic_account_id = fields.Many2many('account.analytic.account', string='Analytic Accounts')

    def btn_print(self):
        return self.env.ref('sale_analysis_report.sale_analysis_excel_report').report_action(self, data={
            'date_from': self.date_from,
            'date_to': self.date_to,
            'analytic_account_id': self.analytic_account_id.ids
        })
