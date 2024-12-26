# -*- coding: utf-8 -*-

from odoo import fields, models, api


class DamageLocation(models.Model):

    _name = "damage.condition"
    _description = "Damage Condition"

    name = fields.Char(string="Damage", required=True)
    damage_code = fields.Char(string="Code", required=True)
    active = fields.Boolean(string="Active", default=True)
    company_id = fields.Many2one("res.company")

    @api.depends("name", "damage_code")
    def _compute_display_name(self):
        if self._context.get('is_move_in_damage'):
            for record in self:
                record.display_name = record.name
                if record.damage_code:
                    record.display_name = f"{record.name}" + f" ({record.damage_code})"
        else:
            for record in self:
                record.display_name = record.name
