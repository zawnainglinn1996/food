odoo.define('pos_slip_extend.models', function(require){

var models = require('point_of_sale.models');

models.load_models([
    {
        label: 'Counter Logo',
        loaded: function (self) {
            self.config.logo = `data:image/png;base64,${self.config.logo}`;
        },
    },
]);
var superOrder = models.Order.prototype;
models.Order = models.Order.extend({
     export_for_printing: function () {
            var receipt = superOrder.export_for_printing.call(this);
            if (this.table){
                var floor = this.table['floor'] ? this.table['floor']['name'] : '';
                receipt.table_no =floor +'/' + this.table['name'];
            }else{
                receipt.table_no = this.table_no;
            }
            return receipt
        },

});

return models;

});