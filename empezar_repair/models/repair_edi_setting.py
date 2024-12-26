# -*- coding: utf-8 -*-
from odoo import fields, models


class RepairEdiSetting(models.Model):
    _name = "repair.edi.setting"
    _description = "Repair EDI Setting"

    is_dry_edi = fields.Boolean("Is DRY EDI")
    is_repair_completion = fields.Boolean("Is Repair Completion")
    header = fields.Text("Header")
    body = fields.Text("Body")
    footer = fields.Text("Footer")
