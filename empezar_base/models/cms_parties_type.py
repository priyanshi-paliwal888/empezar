# -*- coding: utf-8 -*-

from odoo import fields, models


class CmsPartiesType(models.Model):

    _name = "cms.parties.type"
    _description = "CMS Parties Type"

    name = fields.Char("Name")
    company_id = fields.Many2one(
        "res.company",
        required=True,
        readonly=True,
        default=lambda self: self.env.company,
    )
