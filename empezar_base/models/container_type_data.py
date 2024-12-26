# -*- coding: utf-8 -*-

import logging
from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class ContainerTypeData(models.Model):

    _name = "container.type.data"
    _description = "Container Type Data"

    name = fields.Char("Container Name")
    type_group_code = fields.Char("Group Type Code")
    company_size_type_code = fields.Char("Company Size Type Code")
    te_us = fields.Float("Te-Us")
    order_number = fields.Integer("Order Number")
    is_refer = fields.Selection([("yes", "Yes"), ("no", "No")])
    size = fields.Char("Size")
    is_containerized_product = fields.Boolean("Is Containerized Product", default=False)
    active = fields.Boolean("Active", default=True)
    company_id = fields.Many2one("res.company")

    @api.depends("name", "company_size_type_code")
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.name
            if record.company_size_type_code:
                record.display_name += f" ({record.company_size_type_code})"
