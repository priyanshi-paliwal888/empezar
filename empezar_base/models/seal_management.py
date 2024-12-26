# -*- coding: utf-8 -*-

from odoo import fields, models


class SealManagement(models.Model):

    _name = "seal.management"
    _description = "Seal"
    _rec_name = "seal_number"

    shipping_line_id = fields.Many2one(
        "res.partner",
        domain="[('is_shipping_line', '=', True)]",
        string="Shipping Line",
        required=True,
    )
    shipping_line_logo = fields.Binary(
        string="Shipping Line", related="shipping_line_id.logo"
    )
    location = fields.Many2one(
        "res.company",
        string="Location",
        domain="[('parent_id','!=', False)]",
        required=True,
    )
    seal_number = fields.Char(string="Seal No.", translate=True, required=True)
    container_number = fields.Char(string="Container No.", default="-")
    rec_status = fields.Selection(
        [
            ("available", "Available"),
            ("used", "Used"),
            ("damaged", "Damaged"),
        ],
        default="available",
        string="Status",
    )

    _sql_constraints = [
        ("seal_number_uniq", "unique(seal_number, location, shipping_line_id)", "Seal Number already Present")
    ]