# -*- coding: utf-8 -*-
from odoo import fields, models


class UnlinkReason(models.Model):
    _name = "unlink.reason"
    _description = "Unlink Reason"
    _rec_name = 'reason'

    reason = fields.Char("Unlink Reason")
    update_quantity = fields.Boolean("Update Quantity", default=False,required=True)
