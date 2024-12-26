# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, tools, _
from odoo.addons.web.controllers.home import ensure_db, Home, SIGN_UP_REQUEST_PARAMS, LOGIN_SUCCESSFUL_PARAMS


class CustomHome(Home):

    @http.route()
    def web_login(self, *args, **kw):
        """
        Change the user login error message.
        :param args:
        :param kw:
        :return:
        """
        ensure_db()
        response = super().web_login(*args, **kw)
        if response.qcontext.get('error'):
            response.qcontext.update({'error': 'Username or password is incorrect'})
        return response
