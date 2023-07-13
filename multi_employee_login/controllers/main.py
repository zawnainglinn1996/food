# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _
from odoo.http import request
from odoo.addons.web.controllers.main import Home


class login_employee(Home):

    @http.route()
    def web_login(self, *args, **kw):
        call_super = super(login_employee, self).web_login(*args, **kw)
        if request.params.get("login_success"):
            if request.env.user and request.env.user.is_concurrent_user:
                act = request.env.ref('multi_employee_login.action_hr_employee_login')
                return request.redirect('/web#action=%s' % str(act.id))
            else:
                request.session.emp_id = request.env.user.employee_id.id
        return call_super
