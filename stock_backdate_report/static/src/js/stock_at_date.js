odoo.define('stock_backdate_report.stock_at_date_controller', function(require){

'use strict';

var ListController = require('web.ListController');

var BackdateListController = ListController.extend({

    buttons_template: 'StockAtDateButtons',

    init: function (parent, model, renderer, params) {
        this.context = renderer.state.getContext();
        return this._super.apply(this, arguments);
    },

    renderButtons: function ($node) {
        this._super.apply(this, arguments);
        this.$buttons.on('click', '.btn-show-stock-at-date-wizard', this.showStockAtDateWizard.bind(this));
    },

    showStockAtDateWizard: async function () {
        return this.do_action({
            name: 'Backdate Location-Wise Report',
            type: 'ir.actions.act_window',
            res_model: 'stock.backdate.report.wizard',
            views: [[false, 'form']],
            view_mode: 'form',
            target: 'new',
        });
    },

});

return BackdateListController;

});

odoo.define('stock_backdate_report.stock_at_date_view', function(require){

'use strict';

var ListView = require('web.ListView');
var stockAtDateController = require('stock_backdate_report.stock_at_date_controller');
var viewRegistry = require('web.view_registry');

var StockAtDateLocationWiseView = ListView.extend({
    config: _.extend({}, ListView.prototype.config, {
        Controller: stockAtDateController,
    }),
});

viewRegistry.add('stock_at_date_location_wise', StockAtDateLocationWiseView);

return StockAtDateLocationWiseView;

});
