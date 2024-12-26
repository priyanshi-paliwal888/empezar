# -*- coding: utf-8 -*-
from odoo import fields, models

class MasterComponent(models.Model):
    _name = "master.component"
    _description = "Master Component"
    _rec_name = "code"
    """Model to store the master component."""

    code = fields.Char("Code")
    name = fields.Char("Name")
    description = fields.Char("Description")
