from odoo import models, fields, api, _
import pytz
from datetime import datetime
from dateutil import relativedelta
from dateutil.relativedelta import relativedelta
from itertools import groupby
from operator import itemgetter


class ProfitLossExcelReport(models.AbstractModel):
    _name = 'report.profit_and_loss_by_branch.profit_loss_excel_report'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Profit & Loss Report'

    @api.model
    def _get_other_income_lines(self, options):
        date_from = options.get('date_from')
        date_to = options.get('date_to')
        analytic_account_ids = options['analytic_account_id']

        domain = [('date', '>=', date_from), ('date', '<=', date_to),
                  ('move_id.state', 'not in', ['draft', 'cancel']),
                  ('analytic_account_id', 'in', analytic_account_ids)]

        income_journal_ids = self.env['account.move.line'].search(domain)
        journal_lines = []
        other_income_lines = income_journal_ids.filtered(lambda l: l.account_id.user_type_id.name == 'Other Income')

        lines = other_income_lines.sorted(key=lambda l: (l.account_id.id, l.analytic_account_id.id))

        for key, grouped_lines in groupby(lines, lambda l: (l.account_id.id, l.analytic_account_id.id)):
            first_line = False
            credit_amount = 0
            debit_amount = 0
            for line in grouped_lines:
                credit_amount += line.credit
                debit_amount += line.debit
                first_line = line
            journal_lines.append({
                'account_name': first_line.account_id.code + ' ' + first_line.account_id.name or '',
                'analytic_account_id': first_line.analytic_account_id.id or 0,
                'credit_amount': credit_amount - debit_amount,
                'account_type': first_line.account_id.user_type_id.name or '',
            })

        return journal_lines

    @api.model
    def _get_cogs_lines(self, options):
        date_from = options.get('date_from')
        date_to = options.get('date_to')
        analytic_account_ids = options['analytic_account_id']

        domain = [('date', '>=', date_from), ('date', '<=', date_to),
                  ('move_id.state', 'not in', ['draft', 'cancel']),
                  ('analytic_account_id', 'in', analytic_account_ids)]

        income_journal_ids = self.env['account.move.line'].search(domain)
        journal_lines = []
        cogs_line_ids = income_journal_ids.filtered(lambda l: l.account_id.user_type_id.name == 'Cost of Revenue')

        lines = cogs_line_ids.sorted(key=lambda l: (l.account_id.id, l.analytic_account_id.id))

        for key, grouped_lines in groupby(lines, lambda l: (l.account_id.id, l.analytic_account_id.id)):
            first_line = False
            debit_amount = 0
            credit_amount = 0
            for line in grouped_lines:
                debit_amount += line.debit
                credit_amount += line.credit
                first_line = line
            journal_lines.append({
                'account_name': first_line.account_id.code + ' ' + first_line.account_id.name or '',
                'analytic_account_id': first_line.analytic_account_id.id or 0,
                'debit_amount': debit_amount - credit_amount,
                'account_type': first_line.account_id.user_type_id.name or '',
            })

        return journal_lines

    @api.model
    def _get_data(self, options):
        date_from = options.get('date_from')
        date_to = options.get('date_to')
        analytic_account_ids = options['analytic_account_id']

        domain = [('date', '>=', date_from), ('date', '<=', date_to),
                  ('move_id.state', 'not in', ['draft', 'cancel']),
                  ('analytic_account_id', 'in', analytic_account_ids)]

        income_journal_ids = self.env['account.move.line'].search(domain)

        journal_lines = []
        income_journal_line_ids = income_journal_ids.filtered(lambda l: l.account_id.user_type_id.name == 'Income')
        lines = income_journal_line_ids.sorted(key=lambda l: (l.account_id.id, l.analytic_account_id.id))

        for key, grouped_lines in groupby(lines, lambda l: (l.account_id.id, l.analytic_account_id.id)):
            first_line = False
            credit_amount = 0
            debit_amount = 0
            for line in grouped_lines:
                credit_amount += line.credit
                debit_amount += line.debit
                first_line = line

            journal_lines.append({
                'account_name': first_line.account_id.code + ' ' + first_line.account_id.name or '',
                'analytic_account_id': first_line.analytic_account_id.id or 0,
                'credit_amount': credit_amount - debit_amount,
                'account_type': first_line.account_id.user_type_id.name or '',
            })

        return journal_lines

    @api.model
    def _get_expense_lines(self, options):
        date_from = options.get('date_from')
        date_to = options.get('date_to')
        analytic_account_ids = options['analytic_account_id']

        domain = [('date', '>=', date_from), ('date', '<=', date_to),
                  ('move_id.state', 'not in', ['draft', 'cancel']),
                  ('analytic_account_id', 'in', analytic_account_ids)]

        income_journal_ids = self.env['account.move.line'].search(domain)
        journal_lines = []
        expense_line_ids = income_journal_ids.filtered(lambda l: l.account_id.user_type_id.name == 'Expenses')
        lines = expense_line_ids.sorted(key=lambda l: (l.account_id.id, l.analytic_account_id.id))

        for key, grouped_lines in groupby(lines, lambda l: (l.account_id.id, l.analytic_account_id.id)):
            first_line = False
            debit_amount = 0
            credit_amount = 0
            for line in grouped_lines:
                debit_amount += line.debit
                credit_amount += line.credit
                first_line = line
            journal_lines.append({
                'account_name': first_line.account_id.code + ' ' + first_line.account_id.name or '',
                'analytic_account_id': first_line.analytic_account_id.id or 0,
                'debit_amount': debit_amount - credit_amount,
                'account_type': first_line.account_id.user_type_id.name or '',
            })

        return journal_lines

    @api.model
    def _get_depreciation_lines(self, options):
        date_from = options.get('date_from')
        date_to = options.get('date_to')
        analytic_account_ids = options['analytic_account_id']

        domain = [('date', '>=', date_from), ('date', '<=', date_to),
                  ('move_id.state', 'not in', ['draft', 'cancel']),
                  ('analytic_account_id', 'in', analytic_account_ids)]

        income_journal_ids = self.env['account.move.line'].search(domain)
        journal_lines = []
        depreciation_line_ids = income_journal_ids.filtered(lambda l: l.account_id.user_type_id.name == 'Depreciation')
        lines = depreciation_line_ids.sorted(key=lambda l: (l.account_id.id, l.analytic_account_id.id))

        for key, grouped_lines in groupby(lines, lambda l: (l.account_id.id, l.analytic_account_id.id)):
            first_line = False
            debit_amount = 0
            credit_amount = 0
            for line in grouped_lines:
                debit_amount += line.debit
                credit_amount += line.credit
                first_line = line
            journal_lines.append({
                'account_name': first_line.account_id.code + ' ' + first_line.account_id.name or '',
                'analytic_account_id': first_line.analytic_account_id.id or 0,
                'debit_amount': debit_amount - credit_amount,
                'account_type': first_line.account_id.user_type_id.name or '',
            })

        return journal_lines

    def generate_xlsx_report(self, workbook, data, docs):
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        analytic_account_ids = data.get('analytic_account_id')

        analytic_account_name = []
        for analytic in analytic_account_ids:
            analytic_id = self.env['account.analytic.account'].browse(analytic)
            analytic_account_name.append(analytic_id.name)
        separator = ', '
        analytic_name = separator.join(analytic_account_name)
        y_offset = 0
        x_offset = 0

        format0 = workbook.add_format({
            'bold': True, 'align': 'center', 'font_size': 15,
            'bg_color': '#B0C4DE', 'valign': 'vcenter', 'border': True,
        })

        format1 = workbook.add_format({
            'bold': True, 'border': True, 'align': 'center', 'font_size': 13, 'valign': 'vcenter',
        })
        format6 = workbook.add_format({
            'bold': True, 'border': True, 'align': 'right', 'font_size': 13, 'valign': 'vcenter',
        })

        format2 = workbook.add_format({
            'bold': True, 'border': True, 'align': 'center', 'font_size': 13, 'valign': 'vcenter',
        })
        format3 = workbook.add_format({
            'bold': True, 'border': True, 'align': 'left', 'font_size': 13, 'valign': 'vcenter',
        })
        format4 = workbook.add_format({
            'align': 'right', 'border': True, 'valign': 'vcenter', 'font_size': 12,
        })
        format5 = workbook.add_format({
            'align': 'left', 'border': True, 'valign': 'vcenter', 'font_size': 12, })
        lines = self._get_data(data)
        cogs_lines = self._get_cogs_lines(data)
        sheet = workbook.add_worksheet('Profit & Loss By Branch')
        sheet.set_row(0, 30)
        sheet.set_row(1, 25)
        sheet.set_row(2, 15)
        sheet.set_row(3, 20)
        sheet.set_row(4, 15)

        sheet.set_column('A:A', 40)
        sheet.set_column('B:B', 25)
        sheet.set_column('C:C', 25)
        sheet.set_column('D:D', 25)
        sheet.set_column('E:E', 25)
        sheet.set_column('F:F', 25)
        sheet.set_column('G:G', 25)
        sheet.set_column('H:H', 25)
        sheet.set_column('I:I', 25)
        sheet.set_column('J:Z', 25)
        analytic_length = len(analytic_account_ids) + 1
        sheet.merge_range(y_offset, 0, y_offset, analytic_length, _('Profit & Loss By Branch'), format0)
        y_offset += 1
        x_offset += 1

        shop_list = []
        for num in range(len(analytic_account_ids)):
            if num < len(analytic_account_ids):
                analytic_name = self.env['account.analytic.account'].browse(analytic_account_ids[num]).name
                shop_list.append({'analytic_account_id': analytic_account_ids[num], 'x_offset': x_offset,
                                  'account_name': analytic_name})
                sheet.write(y_offset, x_offset, analytic_name, format1)
                x_offset += 1
        sheet.write(y_offset, x_offset, "Balance", format1)
        sheet.write('A3', 'INCOME', format2)
        sheet.write('A4', 'Operating Income', format3)
        row_index = 5
        updated_shop_name = []
        first_time = False
        total_balance_amt = 0

        """INCOME LINES """
        for line in lines:
            balances = list(filter(lambda record: record['account_name'] == line['account_name'], lines))
            balance_amt = sum(item['credit_amount'] for item in balances)

            if line['account_name'] not in updated_shop_name:
                total_balance_amt += balance_amt
                sheet.write(f'A{row_index}', line['account_name'], format5)
                result_income = {}
                for account_name in set(d['account_name'] for d in lines):
                    result_income[account_name] = list(filter(lambda x: x['account_name'] == account_name, lines))
                sheet.write(row_index - 1, len(analytic_account_ids) + 1, format(balance_amt, ",") or 0, format4)

                sheet.write(row_index, len(analytic_account_ids) + 1,format(total_balance_amt, ",") or 0, format6)
                updated_shop_name.append(line['account_name'])

                for rec in shop_list:
                    datas = list(filter(
                        lambda record: record['analytic_account_id'] == rec['analytic_account_id'] and record[
                            'account_name'] == line['account_name'], lines))
                    amount = sum(item['credit_amount'] for item in datas)
                    income_offset = rec['x_offset']

                    sheet.write(row_index - 1, income_offset, format(amount, ",") or 0, format4)

                    map_analytic_accounts = list(
                        filter(lambda record: record['analytic_account_id'] == rec['analytic_account_id'], lines))
                    total_value = sum(item['credit_amount'] for item in map_analytic_accounts)

                    total_row_index = row_index
                    if not first_time:
                        sheet.write(total_row_index + len(result_income)-1 if len(result_income) > 1 else total_row_index,
                                    income_offset, format(total_value, ",") or 0, format6)
                first_time = True
                row_index += 1
        sheet.write(f'A{row_index}', 'Total Operating Income', format3)
        row_index += 1
        sheet.write(f'A{row_index}', 'COST OF REVENUE', format1)
        row_index += 1

        """COGS LINES REVENUE"""
        total_revenue = 0
        first_time_revenue = False
        for cogs in cogs_lines:
            balances_revenue = list(filter(lambda record: record['account_name'] == cogs['account_name'], cogs_lines))
            total_balance_amt_revenue = sum(item['debit_amount'] for item in balances_revenue)

            if cogs['account_name'] not in updated_shop_name:
                total_revenue += total_balance_amt_revenue
                sheet.write(f'A{row_index}', cogs['account_name'], format5)
                result_cogs = {}
                for account_name in set(d['account_name'] for d in cogs_lines):
                    result_cogs[account_name] = list(filter(lambda x: x['account_name'] == account_name, cogs_lines))
                sheet.write(row_index - 1, len(analytic_account_ids) + 1, format(total_balance_amt_revenue, ",") or 0,
                            format4)
                sheet.write(row_index, len(analytic_account_ids) + 1, format(total_revenue, ",") or 0, format6)
                updated_shop_name.append(cogs['account_name'])

                for rec in shop_list:
                    datas = list(filter(
                        lambda record: record['analytic_account_id'] == rec['analytic_account_id'] and record[
                            'account_name'] == cogs['account_name'], cogs_lines))
                    amount_revenue = sum(item['debit_amount'] for item in datas)
                    income_offset = rec['x_offset']
                    sheet.write(row_index - 1, income_offset, format(amount_revenue, ",") or 0, format4)

                    map_analytic_accounts = list(
                        filter(lambda record: record['analytic_account_id'] == rec['analytic_account_id'], cogs_lines))
                    total_value_revenue = sum(item['debit_amount'] for item in map_analytic_accounts)
                    total_row_index_revenue = row_index
                    if not first_time_revenue:
                        sheet.write(total_row_index_revenue + len(result_cogs) -1 if len(result_cogs) > 1 else total_row_index_revenue,
                                    income_offset, format(total_value_revenue, ",") or 0, format6)
                first_time_revenue = True
                row_index += 1
        sheet.write(f'A{row_index}', 'Total Cost Of Revenue', format3)
        row_index += 1

        """FOR GROSS PROFIT"""
        sheet.write(f'A{row_index}', 'Total Gross Profit', format3)
        total_gross_profit_balance = 0
        for rec in shop_list:
            cogs_data = list(filter(lambda x: x['analytic_account_id'] == rec['analytic_account_id'], cogs_lines))
            total_cogs_debit_amount = sum(item['debit_amount'] for item in cogs_data)


            income_datas = list(filter(lambda x: x['analytic_account_id'] == rec['analytic_account_id'], lines))
            total_income_amount = sum(item['credit_amount'] for item in income_datas)
            income_offset = rec['x_offset']
            # total_gross_profit = total_income_amount + total_other_income_amount - total_cogs_debit_amount FROM NILAR REQUEST
            total_gross_profit = total_income_amount - total_cogs_debit_amount

            total_gross_profit_balance += total_gross_profit
            sheet.write(row_index - 1, income_offset, format(total_gross_profit, ",") or 0, format6)

        sheet.write(row_index - 1, len(analytic_account_ids) + 1, format(total_gross_profit_balance, ",") or 0, format6)
        row_index += 1


        sheet.write(f'A{row_index}', 'OTHER INCOME', format1)
        row_index += 1




        """Other Income  Lines"""

        other_income_lines = self._get_other_income_lines(data)
        total_other_income_amt = 0
        first_time_o_income = False
        count_account_name = 0
        for o_income in other_income_lines:
            balances_other_income = list(
                filter(lambda record: record['account_name'] == o_income['account_name'], other_income_lines))
            other_income_amount = sum(item['credit_amount'] for item in balances_other_income)

            if o_income['account_name'] not in updated_shop_name:
                total_other_income_amt += other_income_amount
                sheet.write(f'A{row_index}', o_income['account_name'], format5)
                count_account_name += 1

                result = {}
                for account_name in set(d['account_name'] for d in other_income_lines):
                    result[account_name] = list(filter(lambda x: x['account_name'] == account_name, other_income_lines))
                sheet.write(row_index - 1, len(analytic_account_ids) + 1, format(other_income_amount, ",") or 0,
                            format4)
                sheet.write(row_index, len(analytic_account_ids) + 1, format(total_other_income_amt, ",") or 0, format6)
                updated_shop_name.append(o_income['account_name'])

                for rec in shop_list:
                    datas = list(filter(
                        lambda record: record['analytic_account_id'] == rec['analytic_account_id'] and record[
                            'account_name'] == o_income['account_name'], other_income_lines))
                    other_amount = sum(item['credit_amount'] for item in datas)
                    income_offset = rec['x_offset']
                    sheet.write(row_index - 1, income_offset, format(other_amount, ",") or 0, format4)

                    map_analytic_accounts = list(
                        filter(lambda record: record['analytic_account_id'] == rec['analytic_account_id'],
                               other_income_lines))
                    total_value_amount = sum(item['credit_amount'] for item in map_analytic_accounts)
                    other_income_row_index = row_index
                    if not first_time_o_income:

                        sheet.write(other_income_row_index + len(result)-1 if len(result)>1 else other_income_row_index, income_offset, format(total_value_amount, ",") or 0,
                                    format6)

                first_time_o_income = True
                row_index += 1
        sheet.write(f'A{row_index}', 'Total Other Income Amount', format3)
        row_index += 1

        sheet.write(f'A{row_index}', 'Total Income', format3)

        """TOTAL CREDIT SUM FROM INCOME LINE AND OTHER INCOME LINES """
        credit_sum = {}
        for item in lines:
            if item['analytic_account_id'] in credit_sum:
                credit_sum[item['analytic_account_id']] += item['credit_amount']
            else:
                credit_sum[item['analytic_account_id']] = item['credit_amount']
        for item in other_income_lines:
            if item['analytic_account_id'] in credit_sum:
                credit_sum[item['analytic_account_id']] += item['credit_amount']
            else:
                credit_sum[item['analytic_account_id']] = item['credit_amount']
        total_income_balance_amount = 0
        total_income_value = 0;
        for shop in shop_list:
            analytic_account_id = shop['analytic_account_id']
            total_income_value = credit_sum.get(analytic_account_id)
            if total_income_value:
                total_income_balance_amount += total_income_value
            income_offset = shop['x_offset']
            sheet.write(row_index - 1, income_offset, format(total_income_value, ",") if total_income_value else 0, format6)

        sheet.write(row_index - 1, len(analytic_account_ids) + 1, format(total_income_balance_amount, ",") or 0,
                    format6)
        row_index += 1


        sheet.write(f'A{row_index}', 'EXPENSE', format2)
        row_index += 1

        """FOR EXPENSE LINE"""
        sheet.write(f'A{row_index}', 'Expenses', format3)
        row_index += 1

        expense_lines = self._get_expense_lines(data)
        total_expense = 0
        first_time_expense = False
        for expense in expense_lines:
            expense_datas = list(
                filter(lambda record: record['account_name'] == expense['account_name'], expense_lines))
            total_balance_expense_amt = sum(item['debit_amount'] for item in expense_datas)

            if expense['account_name'] not in updated_shop_name:
                total_expense += total_balance_expense_amt
                sheet.write(f'A{row_index}', expense['account_name'], format5)
                result_expense = {}
                for account_name in set(d['account_name'] for d in expense_lines):
                    result_expense[account_name] = list(
                        filter(lambda x: x['account_name'] == account_name, expense_lines))
                sheet.write(row_index - 1, len(analytic_account_ids) + 1, format(total_balance_expense_amt, ",") or 0,
                            format4)
                sheet.write(row_index, len(analytic_account_ids) + 1, format(total_expense, ",") or 0, format6)
                updated_shop_name.append(expense['account_name'])

                for rec in shop_list:
                    datas = list(filter(
                        lambda record: record['analytic_account_id'] == rec['analytic_account_id'] and record[
                            'account_name'] == expense['account_name'], expense_lines))
                    expense_amount = sum(item['debit_amount'] for item in datas)
                    income_offset = rec['x_offset']
                    sheet.write(row_index - 1, income_offset, format(expense_amount, ",") or 0, format4)

                    map_analytic_accounts = list(
                        filter(lambda record: record['analytic_account_id'] == rec['analytic_account_id'],
                               expense_lines))
                    total_value_expense_amount = sum(item['debit_amount'] for item in map_analytic_accounts)
                    total_row_index_expense = row_index
                    if not first_time_expense:
                        sheet.write(total_row_index_expense + len(result_expense) -1 if len(result_expense) > 1 else total_row_index_expense,
                                    income_offset, format(total_value_expense_amount, ",") or 0, format6)
                first_time_expense = True
                row_index += 1
        sheet.write(f'A{row_index}', 'Total Expense', format3)
        row_index += 1
        sheet.write(f'A{row_index}', 'DEPRECIATION', format1)
        row_index += 1

        """DEPRECIATION LINE DATA"""
        depreciation_lines = self._get_depreciation_lines(data)
        total_depreciation = 0
        first_time_depreciation = False
        for depreciation in depreciation_lines:
            depreciation_datas = list(
                filter(lambda record: record['account_name'] == depreciation['account_name'], depreciation_lines))
            total_balance_depreciation_amt = sum(item['debit_amount'] for item in depreciation_datas)

            if depreciation['account_name'] not in updated_shop_name:
                total_depreciation += total_balance_depreciation_amt
                sheet.write(f'A{row_index}', depreciation['account_name'], format5)
                result_depreciation = {}
                for account_name in set(d['account_name'] for d in depreciation_lines):
                    result_depreciation[account_name] = list(
                        filter(lambda x: x['account_name'] == account_name, depreciation_lines))
                sheet.write(row_index - 1, len(analytic_account_ids) + 1,
                            format(total_balance_depreciation_amt, ",") or 0, format4)
                sheet.write(row_index, len(analytic_account_ids) + 1, format(total_depreciation, ",") or 0, format6)
                updated_shop_name.append(depreciation['account_name'])

                for rec in shop_list:
                    datas = list(filter(
                        lambda record: record['analytic_account_id'] == rec['analytic_account_id'] and record[
                            'account_name'] == depreciation['account_name'], depreciation_lines))
                    depreciation_amount = sum(item['debit_amount'] for item in datas)
                    income_offset = rec['x_offset']
                    sheet.write(row_index - 1, income_offset,format(depreciation_amount, ",")  or 0, format4)

                    map_analytic_accounts = list(
                        filter(lambda record: record['analytic_account_id'] == rec['analytic_account_id'],
                               depreciation_lines))
                    total_value_depreciation_amount = sum(item['debit_amount'] for item in map_analytic_accounts)
                    total_row_index_depreciation = row_index
                    if not first_time_depreciation:
                        sheet.write(total_row_index_depreciation + len(result_depreciation) -1 if len(
                            result_depreciation) > 1 else total_row_index_depreciation,
                                    income_offset,format(total_value_depreciation_amount, ",")   or 0, format6)
                first_time_depreciation = True
                row_index += 1

        sheet.write(f'A{row_index}', 'Total Depreciation', format3)
        row_index += 1
        sheet.write(f'A{row_index}', 'Total Expenses', format3)
        total_expense_balance = 0
        for item in shop_list:
            expense_data = list(
                filter(lambda x: x['analytic_account_id'] == item['analytic_account_id'], expense_lines))
            total_expense_debit_amount = sum(item['debit_amount'] for item in expense_data)

            depreciation_data = list(
                filter(lambda x: x['analytic_account_id'] == item['analytic_account_id'], depreciation_lines))
            total_depreciation_debit_amount = sum(item['debit_amount'] for item in depreciation_data)

            income_offset = item['x_offset']
            total_expense_amt = total_expense_debit_amount + total_depreciation_debit_amount
            total_expense_balance += total_expense_amt
            sheet.write(row_index - 1, income_offset, format(total_expense_amt, ",")   or 0, format6)
        sheet.write(row_index - 1, len(analytic_account_ids) + 1,format(total_expense_balance, ",")   or 0, format6)
        row_index += 1

        sheet.write(f'A{row_index}', 'NET PROFIT', format1)
        total_net_profit_balance = 0
        for net_profit in shop_list:
            net_cogs_data = list(
                filter(lambda x: x['analytic_account_id'] == net_profit['analytic_account_id'], cogs_lines))
            net_cogs_debit_amount = sum(item['debit_amount'] for item in net_cogs_data)

            net_other_income_data = list(
                filter(lambda x: x['analytic_account_id'] == net_profit['analytic_account_id'], other_income_lines))
            net_other_income_amount = sum(item['credit_amount'] for item in net_other_income_data)

            income_datas = list(filter(lambda x: x['analytic_account_id'] == net_profit['analytic_account_id'], lines))
            total_income_amount = sum(item['credit_amount'] for item in income_datas)

            """ FORMULA FOR Total Gross Profit = Income - (COGS + Other Income )"""
            gross_profit = total_income_amount + net_other_income_amount - net_cogs_debit_amount

            expense_data = list(
                filter(lambda x: x['analytic_account_id'] == net_profit['analytic_account_id'], expense_lines))
            total_expense_debit_amount = sum(item['debit_amount'] for item in expense_data)

            depreciation_data = list(
                filter(lambda x: x['analytic_account_id'] == net_profit['analytic_account_id'], depreciation_lines))
            total_depreciation_debit_amount = sum(item['debit_amount'] for item in depreciation_data)

            net_expense_amt = total_expense_debit_amount + total_depreciation_debit_amount

            """NET PROFIT = Gross Profit - (Expense + Depreciation)"""
            net_profit_amount = gross_profit - net_expense_amt
            total_net_profit_balance += net_profit_amount
            income_offset = net_profit['x_offset']
            sheet.write(row_index - 1, income_offset, format(net_profit_amount, ",")  or 0, format6)
        sheet.write(row_index - 1, len(analytic_account_ids) + 1,format(total_net_profit_balance, ",")  or 0, format6)
