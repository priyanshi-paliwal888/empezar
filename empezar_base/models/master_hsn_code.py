# -*- coding: utf-8 -*-

from odoo import fields, models, api


class MasterHSNSACCode(models.Model):

    _name = "master.hsn.code"
    _description = "HSN/SAC Code"

    name = fields.Char("Description", required=True)
    code = fields.Integer("Code", required=True)
    active = fields.Boolean("Active", default=True)
    company_id = fields.Many2one("res.company")

    @api.depends("name", "code")
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.name
            if record.code:
                record.display_name = f"{record.code}" + f" ({record.name})"

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if name:
            args = args or []
            domain = ['|', ('code', operator, name), ('name', operator, name)]
            records = self.search(domain + args, limit=limit)
            return records.name_get()
        return super(MasterHSNSACCode, self).name_search(name, args, operator, limit)
