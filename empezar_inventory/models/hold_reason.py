# -*- coding: utf-8 -*-
from odoo import fields, models


class HoldReason(models.Model):
    _name = "hold.reason"
    _description = "Hold Reason"

    name = fields.Char(string="Hold Reason", required=True)
    active = fields.Boolean(string="Active ", default=True)
    company_id = fields.Many2one("res.company")
