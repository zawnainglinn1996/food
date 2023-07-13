# -*- coding: utf-8 -*-

import math
import re
from odoo import api, models, _
from odoo.exceptions import ValidationError


class ProductAutoBarcode(models.Model):
    _inherit = 'product.product'

    def action_generate_barcode(self):
        for rec in self:
            default_code = '883622'
            if rec.default_code:
                ean = generate_ean(str(default_code + rec.default_code))
                if rec.categ_id.name == 'Finished Goods':
                    if not rec.barcode:

                        rec.write({
                            'barcode': ean
                        })
                else:
                    rec.write({
                        'barcode': rec.default_code
                    })

            else:
                raise ValidationError(_("Internal Reference (IF Code)(%s) does not exists." % rec.name))

    @api.constrains('default_code')
    def check_len_if_code(self):
        for rec in self:
            if rec.categ_id.name == 'Finished Goods':
                if len(rec.default_code) > 6:
                    raise ValidationError(_('Internal Reference (IF Code) should be 6 Digits'))


def ean_checksum(eancode):
    """returns the checksum of an ean string of length 8, returns -1 if
    the string has the wrong length"""
    if len(eancode) != 13:
        return -1
    oddsum = 0
    evensum = 0
    eanvalue = eancode
    reversevalue = eanvalue[::-1]
    finalean = reversevalue[1:]
    for i in range(len(finalean)):
        if i % 2 == 0:
            oddsum += int(finalean[i])
        else:
            evensum += int(finalean[i])
    total = (oddsum * 3) + evensum
    check = int(10 - math.ceil(total % 10.0)) % 10
    return check


def check_ean(eancode):
    """returns True if eancode is a valid ean8 string, or null"""
    if not eancode:
        return True
    if len(eancode) != 13:
        return False
    try:
        int(eancode)
    except:
        return False
    return ean_checksum(eancode) == int(eancode[-1])


def generate_ean(ean):
    """Creates and returns a valid ean8 from an invalid one"""
    if not ean:
        return "0000000000000"
    ean = re.sub("[A-Za-z]", "0", ean)
    ean = re.sub("[^0-9]", "", ean)
    ean = ean[:13]
    if len(ean) < 13:
        ean = ean + '0' * (13 - len(ean))

    return ean[:-1] + str(ean_checksum(ean))


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

class ProductAutoBarcodeInherit(models.Model):
    _inherit = 'product.template'

    @api.constrains('default_code')
    def check_len_if_code(self):
        for rec in self:
            if rec.default_code:
                count = len(rec.default_code)
                if rec.categ_id.name == 'Finished Goods':
                    if count != 6:
                        raise ValidationError(_('Internal Reference (IF Code) should be 6 Digits'))
                else:
                    pass

    def action_generate_barcode(self):
        for rec in self:
            default_code = '883622'

            if rec.default_code:
                if rec.categ_id.name == 'Finished Goods':
                    ean = generate_ean(str(default_code + rec.default_code))
                    if not rec.barcode:
                        rec.write({
                            'barcode': ean
                        })
                else:
                    if not rec.barcode:
                        rec.write({
                            'barcode': rec.default_code,
                        })

            else:
                raise ValidationError(_("Internal Reference (IF Code)(%s) does not exists." % rec.name))
