odoo.define('promotion_program.ApplyPromotionButton', function(require){

    var PosComponent = require('point_of_sale.PosComponent');
    var Registries = require('point_of_sale.Registries');
    var ProductScreen = require('point_of_sale.ProductScreen');
    var { useListener } = require('web.custom_hooks');
    
    class ApplyPromotionButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('click', this.onClick);
        }
        onClick() {
            var promotions = this.env.pos.get_order().applicable_promotions || [];
            promotions.length > 0 ?
                this.showPopup('SelectPromotionPopup', { promotions: promotions }) :
                this.showPopup('ErrorPopup', {
                    title: 'No Promotion Available',
                    body: 'There is no promotion available for current order!'
                });
        }
    }
    
    ProductScreen.addControlButton({
        component: ApplyPromotionButton,
        condition: () => true,
    });
    
    Registries.Component.add(ApplyPromotionButton);
    
    return ApplyPromotionButton;
    
    });