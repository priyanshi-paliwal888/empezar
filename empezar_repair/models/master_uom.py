# -*- coding: utf-8 -*-
from odoo import fields, models

class MasterComponent(models.Model):
    _name = "master.uom"
    _description = "UOM"
    _rec_name = "name"
    """Model to store the master component."""

    name = fields.Char("Measurement")
