# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class ContainerNumber(models.Model):
    _name = "container.number"
    _description = "Container Numbers"

    vessel_booking_id = fields.Many2one("vessel.booking", string="Booking", ondelete='cascade')
    name = fields.Char(string='Container No.')
    unlink_reason = fields.Many2one('unlink.reason',string="Unlink Reason")
    is_unlink = fields.Boolean(default=False)
    is_unlink_non_editable = fields.Boolean(default=False)
