# -*- coding: utf-8 -*-
from odoo import fields, models

class MasterComponent(models.Model):
    _name = "material.type"
    _description = "Material Type"
    _rec_name = "code"
    """Model to store the material type."""

    code = fields.Char("Code")
    name = fields.Char("Name")
    description = fields.Char("Description")
