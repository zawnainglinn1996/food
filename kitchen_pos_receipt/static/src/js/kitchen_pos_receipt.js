odoo.define('kitchen_pos_receipt.OrderChangeReceipt', function(require){
    'use strict';

    var models = require('point_of_sale.models');
    var core = require('web.core');

    var _super_Order = models.Order.prototype;
    models.Order = models.Order.extend({
        computeChanges: function(categories) {
            var changes = _super_Order.computeChanges.apply(this, arguments);
            changes.user_id = this.pos.user.name;
            changes.date = new Date();
            return changes;
        },
    });

    return {
        models: models,
    };
});