# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.addons import decimal_precision as dp


class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    multi_uom_line_id = fields.Many2one('multi.uom.line', 'Multi UOM Line')
    multi_price_unit = fields.Char('Final Price')


class PricelistRecord(models.Model):
    _name = 'pricelist.record'
    _description = 'Purchase Order Record based on Pricelist'

    name = fields.Many2one(
        'res.partner', 'Vendor',
        domain=[('supplier', '=', True)], ondelete='cascade', required=True,
        help="Vendor of this product")
    sequence = fields.Integer(
        'Sequence', default=1, help="Assigns the priority to the list of product vendor.")
    price = fields.Float(
        'Price', default=0.0, digits='Product Price',
        required=True, help="The price to purchase a product")
    subtotal = fields.Float(
        'Total Price', default=0.0, digits='Product Line Total Price',
        required=True, help="Total price to purchase a product line")
    currency_id = fields.Many2one(
        'res.currency', 'Currency',
        default=lambda self: self.env.user.company_id.currency_id.id,
        required=True)
    multi_uom_line_id = fields.Many2one('multi.uom.line', 'Multi UOM Line')
    product_tmpl_id = fields.Many2one(
        'product.product', 'Product',
        index=True, ondelete='cascade')
    # index=True, ondelete='cascade', oldname='product_id')
    ticket_date = fields.Datetime(string="Ticket Date")
    ticket_number = fields.Char(string="PO Number", required=True)
    purchase_qty = fields.Integer(string="Purchase Quantity")


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def button_confirm(self):
        product_supplierinfo = self.env['product.supplierinfo']
        # import pdb
        # pdb.set_trace()
        for order in self:
            if order.state not in ['verified']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order.company_id.po_double_validation == 'one_step' \
                    or (order.company_id.po_double_validation == 'two_step' \
                        and order.amount_total < self.env.user.company_id.currency_id._convert(
                        order.company_id.po_double_validation_amount, order.currency_id, order.company_id,
                        order.date_order or fields.Date.today())) \
                    or order.user_has_groups('purchase.group_purchase_manager'):
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
            for line in order.order_line:
                if line.display_type:
                    continue
                values = {
                    'name': order.partner_id.id,
                    'ticket_number': order.name,
                    'ticket_date': order.date_order,
                    'currency_id': order.currency_id.id,
                    'product_tmpl_id': line.product_id.id,
                    'price': line.multi_price_unit,
                    'subtotal': line.price_subtotal,
                    'multi_uom_line_id': line.multi_uom_line_id.id,
                    'purchase_qty': line.purchase_uom_qty,
                }
                self.env['pricelist.record'].create(values)
                query = """UPDATE product_template SET final_purchase_price=""" + str(
                    line.multi_price_unit) + """ WHERE
                    id=""" + str(line.product_id.product_tmpl_id.id) + """;"""
                self.env.cr.execute(query)

                price = """UPDATE product_supplierinfo SET multi_price_unit=""" + str(line.multi_price_unit) + """ 
                WHERE name=""" + str(line.partner_id.id) + """ AND product_tmpl_id=""" + str(line.product_id.product_tmpl_id.id) + """;"""
                self.env.cr.execute(price)

                uom = """UPDATE product_supplierinfo SET multi_uom_line_id=""" + str(line.multi_uom_line_id.id) + """ 
                WHERE name=""" + str(line.partner_id.id) + """ AND product_tmpl_id=""" + str(line.product_id.product_tmpl_id.id) + """;"""
                self.env.cr.execute(uom)
        return True


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def action_stock_replenishment_info(self):
        records = self.env['pricelist.record'].search([('product_tmpl_id.name', '=', self.product_id.name)],
                                                      order='ticket_date desc', limit=5)
        info_line = {
            'name': 'Final Purchase Pricelist History',
            'type': 'ir.actions.act_window',
            'res_model': 'pricelist.record',
            'target': 'new',
            'context': {'tree_view_ref': 'pricelist_record_tree_view'},
            'domain': [('id', 'in', records.ids)],
            'view_mode': 'tree',
        }
        return info_line


class ProductTemplate(models.Model):
    _inherit = "product.template"

    final_purchase_price = fields.Float("Final Purchase Price")
