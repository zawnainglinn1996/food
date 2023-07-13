from odoo import api, models, fields, _
from datetime import timedelta
from odoo.exceptions import UserError


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    def get_sale_order_slip_report(self):
        records = []
        for order in self:
            contact = False
            child_ids = order.partner_id.child_ids
            contact_phone = ''
            for con in child_ids:
                if con.type == 'contact':
                    contact = con.name
                    contact_phone = con.phone

            sale_order_template_id = []
            for temp in order.sale_order_template_id.sale_order_template_option_ids:
                sale_order_template_id.append({
                    'product': temp.product_id.name,
                    'description': temp.product_id.name,
                    'qty': temp.quantity,
                    'uom': temp.uom_id.name,
                })

            dis_amt_total = 0
            deposite = 0

            order_line = []
            for line in order.order_line:

                if line.product_id.name == 'Down payment':
                    deposite += line.price_unit
                dis_amt = line.product_uom_qty * line.price_unit * ((line.discount or 0.0) / 100.0)
                order_line.append({
                    'product_name': line.name or '',
                    'uom': line.product_id.uom_id.name or '',
                    'price_unit':  "{:,.0f}".format(line.price_unit) or '0',
                    'qty': line.product_uom_qty or '0',
                    'tax': line.tax_id.name or '',
                    'dis_total': dis_amt_total or '0',
                    'discount': dis_amt or '0',
                    'deposite': deposite or '0',
                    'subtotal': line.price_subtotal or '0',
                })
                dis_amt_total += dis_amt

            remain_balance = order.amount_total - deposite

            if order.team_id:
                sale_team_id = []
                for team in order.team_id:
                    sale_team_id.append({
                        'title_img': team.team_logo,
                        'title_name': team.header,
                    })
            else:
                raise UserError(_('Please Insert Sale Team!!!'))

            records.append({
                'cname': order.partner_id.name or '',
                'street': order.partner_id.street or '',
                'street2': order.partner_id.street2 or '',
                'city': order.partner_id.city or '',
                'phone': order.partner_id.phone or '',
                'contact_name': contact or '',
                'mobile': contact_phone or '',
                'commit_date': order.commitment_date + timedelta(hours=6, minutes=30) or '',
                'actual_start_time': order.actual_start_time or '',
                'vouncer_no': order.name or '',
                'order_date': order.date_order + timedelta(hours=6, minutes=30) or '',
                'order_shop_branch': order.analytic_account_id.name or '',
                'from_shop_ph': order.from_shop_ph or '',
                'to_shop_ph': order.to_shop_ph or '',
                'to_shop_name': order.to_shop_name.name or '',
                'contact_ph': order.contact_ph or '',
                'untaxed_amount':  "{:,.0f}".format(order.amount_untaxed) or 0,
                'amount_tax':   "{:,.0f}".format(order.amount_tax) or 0,
                'amount_total':  "{:,.0f}".format(order.amount_total) or 0 ,
                'dis_amt_total':   "{:,.0f}".format(dis_amt_total) or 0,
                'deposite':    "{:,.0f}".format(deposite) or 0,
                'remain_balance':   "{:,.0f}".format(remain_balance) or 0,
                'order_line': order_line,
                'sale_team_id': sale_team_id,
                'sale_order_template_id': sale_order_template_id,
            })
        return self.env.ref('pos_slip_extend.action_sale_order_slip_report').report_action(self, data={'records': records})
