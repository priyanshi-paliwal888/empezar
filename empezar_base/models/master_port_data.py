# -*- coding: utf-8 -*-

from odoo import fields, models, api


class MasterPortData(models.Model):

    _name = "master.port.data"
    _description = "Master Port Data"
    _rec_name = "port_name"

    country_iso_code = fields.Char("Country ISO Code")
    port_code = fields.Char("Port Code")
    port_name = fields.Char("Port Name")
    state_code = fields.Char("State Code")
    status = fields.Char("Status")
    latitude = fields.Char("Latitude")
    longitude = fields.Char("Longitude")
    popular_port = fields.Boolean("Popular Port")
    active = fields.Boolean("Active", default=True)
    company_id = fields.Many2one("res.company")
    combined_iso_and_port = fields.Char(string='Combined ISO and Port Code', compute='_compute_combined_code',
                                        store=True)

    @api.depends("port_name", "port_code", "country_iso_code")
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.port_name
            if record.country_iso_code or record.port_code:
                details = []
                if record.country_iso_code:
                    details.append(record.country_iso_code)
                if record.port_code:
                    details.append(record.port_code)
                record.display_name += f"({''.join(details)})"

    @api.depends('country_iso_code', 'port_code')
    def _compute_combined_code(self):
        for record in self:
            record.combined_iso_and_port = (record.country_iso_code or '') + (record.port_code or '')

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if name:
            args = args or []
            # Search by port_name or port_code
            domain = ['|', ('port_name', operator, name), ('combined_iso_and_port', operator, name)]
            records = self.search(domain + args, limit=limit)
            return records.name_get()
        return super(MasterPortData, self).name_search(name, args, operator, limit)
