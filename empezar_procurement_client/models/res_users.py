# -*- coding: utf-8 -*-
# Copyright 2016 SYLEAM
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import uuid
from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    is_procurement_user = fields.Boolean(string='Is Procurement User')
    procurement_user_type = fields.Selection(
        string='Procurement user type',
        selection=[('user', 'User'), ('central_authority', 'Central Authority')]
    )
    
    
