import pdb

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import float_is_zero, OrderedSet, float_round, float_repr
from odoo.exceptions import UserError, ValidationError


class Product(models.Model):
    _inherit = 'product.product'

    def _prepare_in_svl_vals_production(self, quantity, unit_cost):
        self.ensure_one()
        company_id = self.env.context.get('force_company', self.env.company.id)
        company = self.env['res.company'].browse(company_id)
        vals = {
            'product_id': self.id,
            'value': company.currency_id.round(unit_cost * quantity),
            'unit_cost': unit_cost,
            'quantity': quantity,
        }
        if self.cost_method in ('average', 'fifo'):
            vals['remaining_qty'] = quantity
            vals['remaining_value'] = vals['value']
        return vals

    def _prepare_out_svl_vals_unbuild(self, quantity, unit_cost):
        """Prepare the values for a stock valuation layer created by a delivery.

        :param quantity: the quantity to value, expressed in `self.uom_id`
        :return: values to use in a call to create
        :rtype: dict
        """
        self.ensure_one()
        company_id = self.env.context.get('force_company', self.env.company.id)
        company = self.env['res.company'].browse(company_id)
        currency = company.currency_id
        # Quantity is negative for out valuation layers.
        quantity = -1 * quantity
        vals = {
            'product_id': self.id,
            'value': currency.round(unit_cost * quantity),
            'unit_cost': unit_cost,
            'quantity': quantity,
        }
        if self.cost_method in ('average', 'fifo'):
            fifo_vals = self._run_fifo(abs(quantity), company)
            vals['remaining_qty'] = fifo_vals.get('remaining_qty')
            # In case of AVCO, fix rounding issue of standard price when needed.
            if self.cost_method == 'average':
                rounding_error = currency.round(unit_cost * self.quantity_svl - self.value_svl)
                if rounding_error:
                    # If it is bigger than the (smallest number of the currency * quantity) / 2,
                    # then it isn't a rounding error but a stock valuation error, we shouldn't fix it under the hood ...
                    if abs(rounding_error) <= (abs(quantity) * currency.rounding) / 2:
                        vals['value'] += rounding_error
                        vals['rounding_adjustment'] = '\nRounding Adjustment: %s%s %s' % (
                            '+' if rounding_error > 0 else '',
                            float_repr(rounding_error, precision_digits=currency.decimal_places),
                            currency.symbol
                        )
            # if self.cost_method == 'fifo':
            #     vals.update(fifo_vals)
        return vals


class StockMove(models.Model):
    _inherit = 'stock.move'

    raw_material_production_line_id = fields.Many2one('mrp.unbuild', 'Components Unbuild')
    byproduct_line_id = fields.Many2one('mrp.unbuild', 'By Product Unbuild')

    def write(self, values):
        res = super(StockMove, self).write(values)
        check_multi_quantity_done = values.get('multi_quantity_done')
        if check_multi_quantity_done:
            mrp_ids = self.env['mrp.production'].search([('procurement_group_id', '=', self.group_id.id)])
            if mrp_ids:
                material_ids = self.env['mrp.bom.material.cost'].search([('mrp_pro_material_id', '=', mrp_ids[0].id)])
                for rec in self:
                    material_id = material_ids.filtered(
                        lambda l: l.product_id.id == rec.product_id.product_tmpl_id.id)
                    material_id.actual_qty = check_multi_quantity_done

        return res

    def _get_price_unit(self):
        if self.production_id and not self.byproduct_id:
            return self.production_id.product_unit_cost
        else:
            return super(StockMove, self)._get_price_unit()

    def _create_in_svl(self, forced_quantity=None):
        """Create a `stock.valuation.layer` from `self`.

        :param forced_quantity: under some circunstances, the quantity to value is different than
            the initial demand of the move (Default value = None)
        """
        svl_vals_list = []
        for move in self:
            move = move.with_company(move.company_id)
            valued_move_lines = move._get_in_move_lines()
            valued_quantity = 0
            for valued_move_line in valued_move_lines:
                valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done,
                                                                                     move.product_id.uom_id)
            unit_cost = abs(move._get_price_unit())  # May be negative (i.e. decrease an out move).
            if move.product_id.cost_method == 'standard':
                unit_cost = move.product_id.standard_price

            if move.production_id and not move.byproduct_id:
                if move.production_id.total_actual_qty:
                    unit_cost = move.production_id.total_actual_all_cost / move.production_id.total_actual_qty

                svl_vals = move.product_id._prepare_in_svl_vals_production(forced_quantity or valued_quantity,
                                                                           unit_cost)
            else:
                svl_vals = move.product_id._prepare_in_svl_vals(forced_quantity or valued_quantity, unit_cost)
            svl_vals.update(move._prepare_common_svl_vals())
            if forced_quantity:
                svl_vals[
                    'description'] = 'Correction of %s (modification of past move)' % move.picking_id.name or move.name
            svl_vals_list.append(svl_vals)
        return self.env['stock.valuation.layer'].sudo().create(svl_vals_list)

    def _create_out_svl(self, forced_quantity=None):
        """Create a `stock.valuation.layer` from `self`.

        :param forced_quantity: under some circunstances, the quantity to value is different than
            the initial demand of the move (Default value = None)
        """
        svl_vals_list = []
        for move in self:
            move = move.with_company(move.company_id)
            valued_move_lines = move._get_out_move_lines()
            valued_quantity = 0
            for valued_move_line in valued_move_lines:
                valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done,
                                                                                     move.product_id.uom_id)
            if float_is_zero(forced_quantity or valued_quantity, precision_rounding=move.product_id.uom_id.rounding):
                continue
            if move.unbuild_id and not move.byproduct_line_id and not move.raw_material_production_line_id:
                unit_cost = move.unbuild_id.mo_id.total_actual_all_cost / move.unbuild_id.mo_id.total_actual_qty
                svl_vals = move.product_id._prepare_out_svl_vals_unbuild(forced_quantity or valued_quantity, unit_cost)
                print(unit_cost, '----------------------------')
            else:
                svl_vals = move.product_id._prepare_out_svl_vals(forced_quantity or valued_quantity, move.company_id)
            svl_vals.update(move._prepare_common_svl_vals())
            if forced_quantity:
                svl_vals[
                    'description'] = 'Correction of %s (modification of past move)' % move.picking_id.name or move.name
            svl_vals['description'] += svl_vals.pop('rounding_adjustment', '')
            svl_vals_list.append(svl_vals)

        return self.env['stock.valuation.layer'].sudo().create(svl_vals_list)

    def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id,
                                       credit_account_id, description):
        self.ensure_one()
        res = super(StockMove, self)._generate_valuation_lines_data(partner_id,
                                                                    qty,
                                                                    debit_value,
                                                                    credit_value,
                                                                    debit_account_id,
                                                                    credit_account_id,
                                                                    description)

        if self.unbuild_id and not self.byproduct_line_id and not self.raw_material_production_line_id:
            lines = []
            unbuild = self.unbuild_id
            if self.location_dest_id.usage == 'production':
                lines.append({
                    'name': description,
                    'product_id': self.product_id.id,
                    'quantity': qty,
                    'product_uom_id': self.product_id.uom_id.id,
                    'partner_id': partner_id,
                    'credit': credit_value if credit_value > 0 else 0,
                    'debit': -credit_value if credit_value < 0 else 0,
                    'account_id': credit_account_id,
                })
                debit = 0
                for material_cost_line in unbuild.mo_id.pro_material_cost_ids:
                    product = self.env['product.product'].search(
                        [('product_tmpl_id', '=', material_cost_line.product_id.id)], limit=1)
                    lines.append({
                        'name': f'{self.reference} {product.name_get()[0][1]}',
                        'product_id': product.id,
                        'quantity': 1,
                        'product_uom_id': product.uom_id.id,
                        'partner_id': partner_id,
                        'credit': 0,
                        'debit': material_cost_line.total_actual_cost,
                        'account_id': material_cost_line.product_id.categ_id.property_stock_account_output_categ_id.id,
                    })
                    debit += material_cost_line.total_actual_cost
                    print(material_cost_line.total_actual_cost, '======================================')

                for labour_cost_line in unbuild.mo_id.pro_labour_cost_ids:
                    account = labour_cost_line.service_product_id.product_tmpl_id.get_product_accounts()['stock_output']
                    lines.append({
                        'name': f'{self.reference} {labour_cost_line.service_product_id.name_get()[0][1]}',
                        'product_id': labour_cost_line.service_product_id.id,
                        'quantity': 1,
                        'product_uom_id': labour_cost_line.service_product_id.uom_id.id,
                        'partner_id': partner_id,
                        'credit': 0,
                        'debit': labour_cost_line.total_actual_cost,
                        'account_id': labour_cost_line.service_product_id.categ_id.property_stock_valuation_account_id.id,
                    })
                    print(labour_cost_line.total_actual_cost, 'Total Actual Cost')
                for overhead_cost_line in unbuild.mo_id.pro_overhead_cost_ids:
                    account = overhead_cost_line.service_product_id.product_tmpl_id.get_product_accounts()[
                        'stock_output']
                    lines.append({
                        'name': f'{self.reference} {overhead_cost_line.service_product_id.name_get()[0][1]}',
                        'product_id': overhead_cost_line.service_product_id.id,
                        'quantity': 1,
                        'product_uom_id': overhead_cost_line.service_product_id.uom_id.id,
                        'partner_id': partner_id,
                        'credit': 0,
                        'debit': overhead_cost_line.total_actual_cost,
                        'account_id': overhead_cost_line.service_product_id.categ_id.property_stock_valuation_account_id.id,
                    })
            else:
                lines.append({
                    'name': description,
                    'product_id': self.product_id.id,
                    'quantity': qty,
                    'product_uom_id': self.product_id.uom_id.id,
                    'partner_id': partner_id,
                    'credit': credit_value if credit_value > 0 else 0,
                    'debit': -credit_value if credit_value < 0 else 0,
                    'account_id': credit_account_id,
                })
                for material_cost_line in unbuild.mo_id.pro_material_cost_ids:
                    product = self.env['product.product'].search(
                        [('product_tmpl_id', '=', material_cost_line.product_id.id)], limit=1)
                    lines.append({
                        'name': f'R-{self.reference} {product.name_get()[0][1]}',
                        'product_id': product.id,
                        'quantity': 1,
                        'product_uom_id': product.uom_id.id,
                        'partner_id': partner_id,
                        'credit': 0,
                        'debit': unbuild.unbuild_material_cost,
                        'account_id': material_cost_line.product_id.categ_id.property_stock_account_output_categ_id.id,
                    })
                for labour_cost_line in unbuild.mo_id.pro_labour_cost_ids:
                    account = labour_cost_line.service_product_id.product_tmpl_id.get_product_accounts()[
                        'stock_output']
                    lines.append({
                        'name': f'R-{self.reference} {labour_cost_line.service_product_id.name_get()[0][1]}',
                        'product_id': labour_cost_line.service_product_id.id,
                        'quantity': 1,
                        'product_uom_id': labour_cost_line.service_product_id.uom_id.id,
                        'partner_id': partner_id,
                        'credit': 0,
                        'debit': labour_cost_line.total_actual_cost,
                        'account_id': labour_cost_line.service_product_id.categ_id.property_stock_valuation_account_id.id,
                    })
                for overhead_cost_line in unbuild.mo_id.pro_overhead_cost_ids:
                    account = overhead_cost_line.service_product_id.product_tmpl_id.get_product_accounts()[
                        'stock_output']
                    lines.append({
                        'name': f'R-{self.reference} {overhead_cost_line.service_product_id.name_get()[0][1]}',
                        'product_id': overhead_cost_line.service_product_id.id,
                        'quantity': 1,
                        'product_uom_id': overhead_cost_line.service_product_id.uom_id.id,
                        'partner_id': partner_id,
                        'credit': 0,
                        'debit': overhead_cost_line.total_actual_cost,
                        'account_id': overhead_cost_line.service_product_id.categ_id.property_stock_valuation_account_id.id,
                    })

            index = 0
            move_lines = {}
            total_debit = 0
            total_credit = 0
            for line in lines:
                total_debit += line['debit']
                total_credit += line['credit']
                move_lines[index] = line
                index += 1
            return move_lines

        if self.production_id and not self.byproduct_id:
            lines = []
            production = self.production_id
            material_loc = production.location_src_id
            if self.location_id.usage == 'production':
                lines.append({
                    'name': description,
                    'product_id': self.product_id.id,
                    'quantity': qty,
                    'product_uom_id': self.product_id.uom_id.id,
                    'partner_id': partner_id,
                    'debit': debit_value if debit_value > 0 else 0,
                    'credit': -debit_value if debit_value < 0 else 0,
                    'account_id': debit_account_id,
                })
                check = 0
                for material_cost_line in production.pro_material_cost_ids:

                    product = self.env['product.product'].search(
                        [('product_tmpl_id', '=', material_cost_line.product_id.id), ('active', '=', True)])
                    if not product:
                        raise UserError(
                            _(" Pls check Product Name - %s ! This Product is Archived") % material_cost_line.product_id.name)
                    lines.append({
                        'name': f'{self.origin} {product.name_get()[0][1]}',
                        'product_id': product.id,
                        'quantity': 1,
                        'product_uom_id': product.uom_id.id,
                        'partner_id': partner_id,
                        'credit': round(material_cost_line.total_actual_cost, 2),
                        'debit': 0,
                        'account_id': material_cost_line.product_id.categ_id.property_stock_account_output_categ_id.id,
                    })
                    check += material_cost_line.total_actual_cost
                    # print('MATERIAL COST ', float_round(material_cost_line.total_actual_cost,
                    #                                     precision_rounding=material_cost_line.multi_uom_line_id.uom_id.rounding))

                for labour_cost_line in production.pro_labour_cost_ids:
                    lines.append({
                        'name': f'{self.origin} {labour_cost_line.service_product_id.name_get()[0][1]}',
                        'product_id': labour_cost_line.service_product_id.id,
                        'quantity': 1,
                        'product_uom_id': labour_cost_line.service_product_id.uom_id.id,
                        'partner_id': partner_id,
                        'credit': round(labour_cost_line.total_actual_cost, 2),
                        'debit': 0,
                        'account_id': labour_cost_line.service_product_id.categ_id.property_stock_valuation_account_id.id,
                    })
                    print(float_round(labour_cost_line.total_actual_cost,
                                      precision_rounding=labour_cost_line.multi_uom_line_id.uom_id.rounding),
                          'Total Actual Cost')
                for overhead_cost_line in production.pro_overhead_cost_ids:
                    lines.append({
                        'name': f'{self.origin} {overhead_cost_line.service_product_id.name_get()[0][1]}',
                        'product_id': overhead_cost_line.service_product_id.id,
                        'quantity': 1,
                        'product_uom_id': overhead_cost_line.service_product_id.uom_id.id,
                        'partner_id': partner_id,
                        'credit': round(overhead_cost_line.total_actual_cost, 2),
                        'debit': 0,
                        'account_id': overhead_cost_line.service_product_id.categ_id.property_stock_valuation_account_id.id,
                    })
                    print(float_round(overhead_cost_line.total_actual_cost,
                                      precision_rounding=overhead_cost_line.multi_uom_line_id.uom_id.rounding), '---')
            else:
                lines.append({
                    'name': description,
                    'product_id': self.product_id.id,
                    'quantity': qty,
                    'product_uom_id': self.product_id.uom_id.id,
                    'partner_id': partner_id,
                    'debit': debit_value if debit_value > 0 else 0,
                    'credit': -debit_value if debit_value < 0 else 0,
                    'account_id': debit_account_id,
                })
                for material_cost_line in production.pro_material_cost_ids:
                    product = self.env['product.product'].search(
                        [('product_tmpl_id', '=', material_cost_line.product_id.id)], limit=1)
                    lines.append({
                        'name': f'R-{self.origin} {product.name_get()[0][1]}',
                        'product_id': product.id,
                        'quantity': 1,
                        'product_uom_id': product.uom_id.id,
                        'partner_id': partner_id,
                        'debit': material_cost_line.total_actual_cost,
                        'credit': 0,
                        'account_id': material_cost_line.product_id.categ_id.property_stock_account_output_categ_id.id,
                    })
                for labour_cost_line in production.pro_labour_cost_ids:
                    lines.append({
                        'name': f'R-{self.origin} {labour_cost_line.service_product_id.name_get()[0][1]}',
                        'product_id': labour_cost_line.service_product_id.id,
                        'quantity': 1,
                        'product_uom_id': labour_cost_line.service_product_id.uom_id.id,
                        'partner_id': partner_id,
                        'debit': labour_cost_line.total_actual_cost,
                        'credit': 0,
                        'account_id': labour_cost_line.service_product_id.categ_id.property_stock_valuation_account_id.id,
                    })
                for overhead_cost_line in production.pro_overhead_cost_ids:
                    lines.append({
                        'name': f'R-{self.origin} {overhead_cost_line.service_product_id.name_get()[0][1]}',
                        'product_id': overhead_cost_line.service_product_id.id,
                        'quantity': 1,
                        'product_uom_id': overhead_cost_line.service_product_id.uom_id.id,
                        'partner_id': partner_id,
                        'debit': overhead_cost_line.total_actual_cost,
                        'credit': 0,
                        'account_id': overhead_cost_line.service_product_id.categ_id.property_stock_valuation_account_id.id,
                    })

            index = 0
            move_lines = {}
            total_debit = 0
            total_credit = 0
            for line in lines:
                total_debit += line['debit']
                total_credit += line['credit']
                move_lines[index] = line
                index += 1
            return move_lines

        return res
