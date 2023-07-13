odoo.define('promotion_program.models', function(require){

var models = require('point_of_sale.models');

models.load_models([
    {
        model: 'promotion.program',
        fields: [
            'name',
            'code',
            'start_date',
            'end_date',
            'company_id',
            'active',
            'type',
            'team_ids',
            'config_ids',
            'buy_one_get_one_line_ids',
            'total_invoice_amount','reward_type','operator','account_id','discount_product_id','product_qty','fixed_discount',
        ],
        domain: function (self) {
            return [['config_ids', 'in', [self.config.id]]];
        },
        loaded: function (self, programs) {
            var today = moment(new Date());
            var promotions_by_id = {};
            var promotions = [];

            for(var program of programs){
                var start_date = program.start_date ? moment(program.start_date, 'YYYY-MM-DD') : false;
                var end_date = program.end_date ? moment(program.end_date, 'YYYY-MM-DD') : false;
                if(
                    (start_date && end_date && today >= start_date && today <= end_date) || 
                    (start_date && !end_date && today >= start_date) || 
                    (!start_date && end_date && today <= end_date) ||
                    (!start_date && !end_date) 
                ){
                    promotions_by_id[program.id] = program;
                    promotions.push(program);
                }
            }
            self.promotions_by_id = promotions_by_id;
            self.promotions = promotions;
        },
    },
    {
        model: 'buy.one.get.one.line',
        fields: [
            'product_x_id', 
            'product_x_qty', 
            'operator', 
            'product_y_id', 
            'product_y_qty', 
            'account_id', 
            'promotion_id'
        ],
        domain: function (self) {
            var promotion_ids = self.promotions.map(promotion => promotion.id);
            return [['promotion_id', 'in', promotion_ids]];
        },
        loaded: function (self, lines) {
            var lines_by_id = {};
            var lines_by_promotion_id = {};
            for(var line of lines){
                var promotion_id = line.promotion_id[0];
                var grouped_lines = lines_by_promotion_id[promotion_id] || [];
                lines_by_id[line.id] = line;
                grouped_lines.push(line);
                lines_by_promotion_id[promotion_id] = grouped_lines;
            }
            self.buy_one_get_one_line_by_id = lines_by_id;
            self.buy_one_get_one_line_by_promotion_id = lines_by_promotion_id;
        },
    },
]);

var superOrder = models.Order.prototype;
models.Order = models.Order.extend({

    set_orderline_options: function(orderline, options) {
        if(options.price_manually_set){
            orderline.price_manually_set = options.price_manually_set;
        }
        var res = superOrder.set_orderline_options.apply(this, arguments);
        if(options.promotion_id){
            orderline.promotion_id = options.promotion_id;
        }
        if(options.promotion_line_id){
            orderline.promotion_line_id = options.promotion_line_id;
        }
        if(options.promotion_description){
            orderline.promotion_description = options.promotion_description;
        }
        if(options.promotion_account_id){
            orderline.promotion_account_id = options.promotion_account_id;
        }
        if(options.remove_before_apply){
            orderline.remove_before_apply = options.remove_before_apply;
        }
        return res;
    },

    add_product: async function(product, options){
        var res = superOrder.add_product.apply(this, arguments);
        this._compute_promotions();
        return res;
    },

    _compute_promotions: function(){
        this._compute_grouped_order_lines();
        this._get_applicable_promotions();
    },

    _compute_grouped_order_lines: function(){
        var grouped_lines = {};
        for(var order_line of this.get_orderlines()){
            var prev_grouped_line = grouped_lines[order_line.product.id];
            var prev_qty = 0, prev_amt = 0, prev_lines = [];
            if(prev_grouped_line){
                prev_qty = prev_grouped_line.qty;
                prev_amt = prev_grouped_line.amt;
                prev_lines = prev_grouped_line.lines;
            }
            prev_lines.push(order_line);
           var qty = prev_qty + order_line.quantity;
           var amt = prev_amt + (order_line.quantity * order_line.price)
           grouped_lines[order_line.product.id] = {
                qty: qty,
                amt: amt,
                lines: prev_lines,
           };
        }
        this.grouped_order_lines = grouped_lines;
        this.order_product_ids = Object.keys(grouped_lines).map(pid => parseInt(pid));
    },

    _add_rewards: function(promotion, applicable_promotions, rewards){
        var prev_rewards = applicable_promotions[promotion.id] || [];
        var all_rewards = prev_rewards.concat(rewards);
        applicable_promotions[promotion.id] = all_rewards;
        return applicable_promotions;
    },

    _get_applicable_promotions: function(){
        var applicable_promotions = [];
        var rewards_by_promotion_id = {};
        var promotions = this.pos.promotions;
        for(var promotion of promotions){
            if(promotion.type === 'buy_one_get_one'){
                var rewards_of_current_promotion = this._apply_buy_one_get_one(promotion);
            }
            if(promotion.type === 'discount_total_amount'){
                var rewards_of_current_promotion = this._apply_discount_total_amount(promotion);
            }
            rewards_by_promotion_id = this._add_rewards(promotion, rewards_by_promotion_id, rewards_of_current_promotion);
        }
        for(var promotion_id of Object.keys(rewards_by_promotion_id)){
            promotion_id = parseInt(promotion_id);
            if(rewards_by_promotion_id[promotion_id].length > 0){
                applicable_promotions.push(this.pos.promotions_by_id[promotion_id]);
            }
        }
        this.applicable_promotions = applicable_promotions;
        this.rewards_by_promotion_id = rewards_by_promotion_id;
        var $applyPromotionButton = $('#apply-promotion-button');
        if(applicable_promotions.length > 0){
            $applyPromotionButton.hasClass('promotions-active') ?
                null :
                $applyPromotionButton.addClass('promotions-active');
        }
        else{
            $applyPromotionButton.hasClass('promotions-active') ?
                $applyPromotionButton.removeClass('promotions-active') :
                null;
        }
    },

    _apply_buy_one_get_one: function(promotion){
        var rewards = [];
        var order_lines = this.grouped_order_lines|| {};

        var lines = this.pos.buy_one_get_one_line_by_promotion_id[promotion.id];
        for(var line of lines){
            var order_line = order_lines[line.product_x_id[0]];
            var order_product_qty = Object.keys(order_lines).reduce(
                (total, product_id) => total+= line.product_x_id.includes(parseInt(product_id)) ? order_lines[(parseInt(product_id))].qty : 0,
                0
            );
            console.log(order_product_qty,'ORDER PRODUCT QUANTITY ORDR ')
            if(!order_line){
                continue
            }
            var already_applied=false;
            for(var order of this.get_orderlines()){
            if(order.promotion_line_id === line.id){
                already_applied = true;
            }
            }

            var qty = line.operator === '=' ?
                        Math.floor(order_line.qty / line.product_x_qty) * line.product_y_qty
                        : line.product_y_qty;

             if(!already_applied && order_product_qty >0){
                 if(line.operator === '='){

                    if(order_product_qty == line.product_x_qty){
                          rewards.push({
                            product: this.pos.db.get_product_by_id(line.product_y_id[0]),
                            price: 0,
                            type: 'foc',
                            qty: qty,
                            promotion_id: promotion.id,
                            promotion_line_id: line.id,
                            promotion_description: `FOC for purchasing ${line.product_x_id[1]}`,
                            promotion_account_id: line.account_id ? line.account_id[0] : false,
                        });

                    }
                 }
                 else{

                   if(order_product_qty >= line.product_x_qty){
                      rewards.push({
                            product: this.pos.db.get_product_by_id(line.product_y_id[0]),
                            price: 0,
                            type: 'foc',
                            qty: qty,
                            promotion_id: promotion.id,
                            promotion_line_id: line.id,
                            promotion_description: `FOC for purchasing ${line.product_x_id[1]}`,
                            promotion_account_id: line.account_id ? line.account_id[0] : false,
                        });
                   }

                 }
             }
        }
        return rewards;
    },

    _apply_discount_total_amount: function(promotion){
        var rewards = [];
        var order_lines = this.grouped_order_lines;
        var total_order = this.get_subtotal()
        var lines = this.orderlines.models;
        var total_order_line = 0


        for (var j = 0; j < lines.length; j++) {
              var line = lines[j];
              if (!line.promotion_id){
                 total_order_line += (line.quantity * line.price)
              }
         }
        var already_applied=false;
        for(var order of this.get_orderlines()){
            if(order.promotion_id === promotion.id){
                already_applied = true;
            }
            }
        if (promotion.operator == '='){

           if (promotion.reward_type == 'discount_amount' && total_order_line == promotion.total_invoice_amount){

                get_total_discount = - ( promotion.fixed_discount);
                if(!already_applied){
                rewards.push({
                    product: this.pos.db.get_product_by_id(promotion.discount_product_id[0]),
                    price: get_total_discount,
                    type: 'discount',
                    qty: 1,
                    promotion_id: promotion.id,
                    promotion_description: `Discount ${promotion.fixed_discount}KS Get Total Order Amount is over ${promotion.total_invoice_amount}`,
                    promotion_account_id: promotion.account_id[0],
                });
                }
            }
           else if (promotion.reward_type =='percentage'  && total_order_line == promotion.total_invoice_amount){
                var check_amount = total_order_line % promotion.total_invoice_amount;
                get_percentage_amount = -(total_order_line * (promotion.fixed_discount /100));
                if(!already_applied){
                rewards.push({
                    product: this.pos.db.get_product_by_id(promotion.discount_product_id[0]),
                    price: get_percentage_amount,
                    type: 'discount',
                    qty: 1,
                    promotion_id: promotion.id,
                    promotion_description: `Discount ${promotion.fixed_discount} % Get  Total Order Amount is over ${promotion.total_invoice_amount} `,
                    promotion_account_id: promotion.account_id[0],
                });
                }
            }
           else{
                 if(total_order_line == promotion.total_invoice_amount){
                     product_qty = promotion.product_qty;
                    if(!already_applied){
                     rewards.push({
                        product: this.pos.db.get_product_by_id(promotion.discount_product_id[0]),
                        price: 0,
                        type: 'foc',
                        qty: product_qty,
                        promotion_id: promotion.id,
                        promotion_description: `Free Product(FOC) Get Total Order Amount is Over ${promotion.total_invoice_amount}`,
                        promotion_account_id: promotion.account_id[0],
                    });
                    }
                 }
           }
        }
        else{
           console.log(total_order_line,promotion.total_invoice_amount,'--------------------------------------------------------------------')
           if (promotion.reward_type == 'discount_amount' && total_order_line >= promotion.total_invoice_amount){
                if(!already_applied){
                rewards.push({
                    product: this.pos.db.get_product_by_id(promotion.discount_product_id[0]),
                    price: - (promotion.fixed_discount),
                    type: 'discount',
                    qty: 1,
                    promotion_id: promotion.id,
                    promotion_description: `Discount ${promotion.fixed_discount} KS Get Total Order Amount is over ${promotion.total_invoice_amount}`,
                    promotion_account_id: promotion.account_id[0],
                });
                }
            }
           else if (promotion.reward_type =='percentage'  && total_order_line >= promotion.total_invoice_amount){
                if(!already_applied){
                rewards.push({
                    product: this.pos.db.get_product_by_id(promotion.discount_product_id[0]),
                    price: -(total_order * promotion.fixed_discount/100),
                    type: 'discount',
                    qty: 1,
                    promotion_id: promotion.id,
                    promotion_description: `Discount ${promotion.fixed_discount} % Get  Total Order Amount is over ${promotion.total_invoice_amount} `,
                    promotion_account_id: promotion.account_id[0],
                });
                }

            }
           else{

                 if(total_order_line >= promotion.total_invoice_amount){
                    if(!already_applied){
                     rewards.push({
                        product: this.pos.db.get_product_by_id(promotion.discount_product_id[0]),
                        price: 0,
                        type: 'foc',
                        qty: promotion.product_qty,
                        promotion_id: promotion.id,
                        promotion_description: `Free Product(FOC) Get Total Order Amount is Over${promotion.total_invoice_amount}`,
                        promotion_account_id: promotion.account_id[0],
                    });
                    }

                 }
           }
        }
        return rewards
    },

    _remove_previous_promotion_lines: function(){
        var lines_to_remove = this.get_orderlines().filter(l => l.remove_before_apply === true);
        for(var line of lines_to_remove){
            this.remove_orderline(line);
        }
    },

});

var superOrderline = models.Orderline.prototype;
models.Orderline = models.Orderline.extend({

    initialize: function(attr, options){
        var res = superOrderline.initialize.apply(this, arguments);
        if(options.promotion_id){
            this.promotion_id = options.promotion_id;
        }
        if(options.promotion_description){
            this.promotion_description = options.promotion_description;
        }
        if(options.promotion_line_id){
            this.promotion_line_id = options.promotion_line_id;
        }
        if(options.promotion_account_id){
            this.promotion_account_id = options.promotion_account_id;
        }
        return res;
    },

    init_from_JSON: function(json) {
        if(json.promotion_id){
            this.promotion_id = json.promotion_id;
        }
        if(json.promotion_description){
            this.promotion_description = json.promotion_description;
        }
        if(json.promotion_line_id){
            this.promotion_line_id = json.promotion_line_id;
        }
        if(json.promotion_account_id){
            this.promotion_account_id = json.promotion_account_id;
        }
        superOrderline.init_from_JSON.apply(this, arguments);
    },

    export_as_JSON: function() {
        var values = superOrderline.export_as_JSON.apply(this, arguments);
        Object.assign(values, {
            promotion_id: this.promotion_id,
            promotion_line_id: this.promotion_line_id,
            promotion_description: this.promotion_description,
            promotion_account_id: this.promotion_account_id,
        })
        return values
    },

    export_for_printing: function(){
            let values = superOrderline.export_for_printing.apply(this, arguments);
            values.promotion_id = this.promotion_id;
            return values;
        },
    
    set_quantity: function(quantity, keep_price){
        var res = superOrderline.set_quantity.apply(this, arguments);
        this.order._compute_promotions();
        return res;
    },

    set_unit_price: function(price){
        var res = superOrderline.set_unit_price.apply(this, arguments);
        this.order._compute_promotions();
        return res;
    },

});

});