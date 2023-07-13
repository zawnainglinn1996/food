odoo.define('multi_uom.listview', function (require) {

    var ListRenderer = require('web.ListRenderer');

    ListRenderer.include({
        _renderHeaderCell: function (node) { 
            var $cell = this._super.apply(this, arguments);
            if (node.attrs && node.attrs.extra_class){
                $cell.addClass(node.attrs.extra_class);
            }   
            return $cell
        }
    })
})