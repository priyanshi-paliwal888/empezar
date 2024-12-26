# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class LoloCharge(models.Model):
    _name = 'lolo.charge.lines'
    _description = 'Lolo Charges'

    container_size = fields.Selection([
        ('20ft', '20FT'),
        ('40ft', '40FT'),
        ('20ft_reefer', '20FT Reefer'),
        ('40ft_reefer', '40FT Reefer'),
    ], string="Container")
    lift_on = fields.Char(string="Lift On", size=12)
    lift_off = fields.Char(string="Lift Off", size=12)
    lolo_charge_id = fields.Many2one("lolo.charge", string="Location", ondelete='cascade')
