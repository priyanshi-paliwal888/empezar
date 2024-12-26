from odoo import models, fields


class CancellationReason(models.Model):

    _name = "cancellation.reason"
    _description = "cancellation_reason"
    _rec_name = "name"

    name = fields.Char("Cancellation Reason")
    active = fields.Boolean(string="Active", default=True)
