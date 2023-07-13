odoo.define('point_of_sale.SelectPromotionPopup', function (require) {
    'use strict';

var AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
var Registries = require('point_of_sale.Registries');

class SelectPromotionPopup extends AbstractAwaitablePopup {
    constructor() {
        super(...arguments);
    }
    selectPromotion(itemId) {
        var $promotionDiv = $('#promotion-item-' + itemId);
        $promotionDiv.hasClass('promotion-selected') ?
            $promotionDiv.removeClass('promotion-selected') :
            $promotionDiv.addClass('promotion-selected')
    }
    applyPromotions(willApplyAll){
        var selectedPromotions = [];
        var order = this.env.pos.get_order();
        var rewards_by_promotion_id = order.rewards_by_promotion_id;
        order._remove_previous_promotion_lines();
        if(!willApplyAll){
            var $selectedPromotionsDiv = $('.promotion-selected');
            for(var $selectedPromotionDiv of $selectedPromotionsDiv){
                selectedPromotions.push($($selectedPromotionDiv).data().id);
            }
        }
        for(var promotion_id of Object.keys(rewards_by_promotion_id)){
            promotion_id = parseInt(promotion_id);
            var rewards = rewards_by_promotion_id[promotion_id];
            if(!willApplyAll && !selectedPromotions.includes(promotion_id)){
                continue
            }
            for(var reward of rewards){
                console.log('RRRRRRRRRRRRRRRRRRRRR',reward)
                if(reward.type === 'discount' || reward.type === 'foc'){
                    order.add_product(reward.product, {
                        price: reward.price,
                        price_manually_set: true,
                        quantity: reward.qty || 1,
                        promotion_id: reward.promotion_id,
                        promotion_line_id: reward.promotion_line_id,
                        promotion_description: reward.promotion_description,
                        remove_before_apply: true,
                        promotion_account_id: reward.promotion_account_id,
                    });
                }
                else if(reward.type === 'price'){
                    for(var order_line of reward.order_lines){
                        order_line.set_unit_price(reward.price);
                    }
                }
            }
        }
        this.confirm();
    }
}
SelectPromotionPopup.template = 'SelectPromotionPopup';
SelectPromotionPopup.defaultProps = {
    promotions: [],
};

Registries.Component.add(SelectPromotionPopup);

return SelectPromotionPopup;
});
