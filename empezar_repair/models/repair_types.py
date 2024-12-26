# -*- coding: utf-8 -*-
from odoo import fields, models

class RepairTypes(models.Model):
    _name = "repair.types"
    _description = "Repair Types"
    _rec_name = "repair_type_code"
    """Model to store the repair types."""

    repair_type_code = fields.Char("Repair Type Code")
    repair_type_name = fields.Char("Name")
    repair_type_description = fields.Char("Description")
    record_status = fields.Selection([
        ('active', 'Active'),
        ('disable', 'Disable'),
            ], string="Status")
