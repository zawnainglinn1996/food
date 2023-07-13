from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_sale_order_a4_report(self):
        orders = []
        for order in self:
            sale_order_template_id = []
            num = len(order.order_line) + 1
            for temp in order.sale_order_template_id.sale_order_template_option_ids:
                sale_order_template_id.append({
                    'product': temp.product_id.name or '',
                    'description': temp.product_id.name or '',
                    'qty': temp.quantity or '0',
                    'uom': temp.uom_id.name or '',
                    'no': num,
                })
                num += 1

            lines = []
            count = 1
            dis_amt_total = 0
            deposite = 0

            for line in order.order_line:
                if line.product_id.name == 'Down payment':
                    deposite += line.price_unit
                dis_amt = line.product_uom_qty * line.price_unit * ((line.discount or 0.0) / 100.0)
                lines.append({
                    'product': line.name or '',
                    'qty': line.product_uom_qty or 0,
                    'price_unit':   "{:,.0f}".format(line.price_unit) or 0,
                    'uom': line.product_id.uom_id.name or '',
                    'subtotal':  "{:,.0f}".format(line.price_subtotal) or 0,
                    'dis_total':  "{:,.0f}".format(dis_amt_total) or 0.00,
                    'deposite': deposite or 0,
                    'no': count,
                })
                count += 1
                dis_amt_total += dis_amt

            if order.team_id:
                sale_team_id = []
                for team in order.team_id:
                    sale_team_id.append({
                        'title_img': team.team_logo,
                        'title_name': team.header,
                    })
            else:
                raise UserError(_('Please Insert Sale Team!!!'))

            remain_balance = order.amount_total - deposite
            orders.append({
                'name': order.name or '',
                'partner_name': order.partner_id.name or '',
                'phone': order.partner_id.phone or '',
                'street': order.partner_id.street or '',
                'order_date': (order.date_order + relativedelta(hours=6, minutes=30)).strftime('%d/%m/%Y %H:%M:%S') or '',
                'shop_name': order.analytic_account_id.name or '',
                'expected_date': (order.commitment_date + relativedelta(hours=6, minutes=30)).strftime('%d/%m/%Y %H:%M:%S') or '',
                'contact_partner_id': order.contact_partner_id or '',
                'contact_ph': order.contact_ph or '',
                'from_shop_ph': order.from_shop_ph or '',
                'to_shop_name': order.to_shop_name.name or '',
                'to_shop_ph': order.to_shop_ph or '',
                'client_name': order.client_name or '',
                'client_related': order.client_related or '',
                'client_phone': order.client_phone or '',
                'actual_start_time': order.actual_start_time or '',
                'amount_total':  "{:,.0f}".format(order.amount_total) or 0.00,
                'amount_tax':  "{:,.0f}".format(order.amount_tax) or 0.00,
                'dis_amt_total':  "{:,.0f}".format(dis_amt_total) or 0.00,
                'deposite': "{:,.0f}".format(deposite) or 0.00,
                'remain_balance': "{:,.0f}".format(remain_balance) or 0.00,
                'lines': lines,
                'sale_team_id': sale_team_id,
                'sale_order_template_id': sale_order_template_id,

            })

        return self.env.ref('report_form.action_report_sale_order_a4').report_action(self, data={'orders': orders})

