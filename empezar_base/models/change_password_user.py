# -*- coding: utf-8 -*-

from odoo import fields, models


class ChangePasswordUser(models.TransientModel):

    _inherit = "change.password.user"

    confirm_passwd = fields.Char(string="Confirm Password", default="")
    show_hide_password = fields.Boolean(string="")
