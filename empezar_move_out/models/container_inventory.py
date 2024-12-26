""" -*- coding: utf-8 -*- """
from odoo import fields, models, api, _


class ContainerInventory(models.Model):

    _inherit = "container.inventory"

    move_in_id = fields.Many2one("move.in", string="Move In", ondelete='cascade')
