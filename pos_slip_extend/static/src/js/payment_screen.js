odoo.define('pos_slip_extend.PaymentScreen', function(require){
    'use strict';

    var PaymentScreen = require('point_of_sale.PaymentScreen');
    var Registries = require('point_of_sale.Registries');

    var PaymentScreenExtend = PaymentScreen => class extends PaymentScreen{
        async validateOrder(isForceValidate) {

            var res = super.validateOrder();
            this.currentOrder.table_no = $('#table-no-id').val();
            return res
        }
    };

    Registries.Component.extend(PaymentScreen, PaymentScreenExtend);

    return PaymentScreenExtend;

});