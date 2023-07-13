odoo.define('multi_employee_login.pos_employees', function (require) {
    "use strict";
var pos_models = require('pos_hr.employees');
var allModels = pos_models.PosModel.prototype.models;
let empIndex;
for(let index=0; index < allModels.length; index++){
    if(allModels[index].model === 'hr.employee'){
        empIndex = index;
        break;
    }
};
if(empIndex){
    allModels[empIndex] = {
    model:  'hr.employee',
    fields: ['name', 'id', 'user_id'],
    domain: function(self){
        return self.config.employee_ids.length > 0
            ? [
                  '&',
                  ['company_id', '=', self.config.company_id[0]],
                  ['id', 'in', self.config.employee_ids],
              ]
            : [['company_id', '=', self.config.company_id[0]]];
    },
    loaded: function(self, employees) {
        if (self.config.module_pos_hr) {
            self.employees = employees;
            self.employee_by_id = {};
            self.employees.forEach(function(employee) {
                self.employee_by_id[employee.id] = employee;
                var hasUser = self.users.some(function(user) {
                    if (user.id === employee.user_id[0]) {
                        employee.role = user.role;
                        return true;
                    }
                    return false;
                });
                if (!hasUser) {
                    employee.role = 'cashier';
                }
            });
        }
    }
};
};

pos_models.PosModel.prototype.models = allModels;
console.log('POS MODELS', pos_models);
return pos_models;

});

