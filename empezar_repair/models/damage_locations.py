# -*- coding: utf-8 -*-
from odoo import fields, models


class DamageLocations(models.Model):
    _name = "damage.locations"
    _description = "Damage Locations"
    _rec_name = "code"
    """Model to store the damage locations."""

    code = fields.Char("Code")
    description = fields.Char("Description")
