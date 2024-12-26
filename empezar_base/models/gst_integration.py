# -*- coding: utf-8 -*-

from odoo import fields, models


class GstIntegration(models.Model):

    _name = "gst.integration"
    _description = "Gst Integration"

    name = fields.Char("Third Party Name")
    api_key = fields.Char("API Key", size=32)
    url = fields.Char("URL")
    integration_status = fields.Selection(
        [
            ("set", "Set"),
            ("not_set", "Not Set"),
        ],
        default="not_set",
    )
    company_id = fields.Many2one(
        "res.company", string="Company Name", ondelete="cascade"
    )
    status = fields.Selection(
        [
            ("active", "Active"),
            ("disable", "Disable"),
        ],
        default="active",
    )
