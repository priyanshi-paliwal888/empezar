# -*- coding: utf-8 -*-
from odoo import fields, models

class DamageType(models.Model):
    _name = "damage.type"
    _description = "Damage Type"
    _rec_name= "damage_type_code"
    """Model to store the damage type."""

    damage_type_code = fields.Char("Damage Type Code")
    damage_type_name = fields.Char("Name")
    damage_type_description = fields.Char("Description")
    record_status = fields.Selection([
        ('active', 'Active'),
        ('disable', 'Disable'),
    ], string="Status")
