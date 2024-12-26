# -*- coding: utf-8 -*-

from odoo import fields, models
from .res_users import ResUsers
from .contrainer_type_edi import ContainerTypeEdi


class ContainerFacilities(models.Model):

    _name = "container.facilities"
    _description = "Container Facilities"

    name = fields.Char(string="Name", size=128, required=True, translate=True)
    facility_type = fields.Selection(
        [("cfs", "CFS"), ("terminal", "Terminal"), ("empty_yard", "Empty Yard")],
        string="Facility Type",
        required=True,
    )
    code = fields.Char("Code", size=10, translate=True)
    port = fields.Many2one("master.port.data", string="Port", required=True)
    port_code = fields.Char(string="Port Code", related="port.port_code")
    port_name = fields.Char(string="Port Code", related="port.port_name")
    port_iso_code = fields.Char(string="Port Code", related="port.country_iso_code")
    port_iso_with_code = fields.Char(string="Port Code", related="port.combined_iso_and_port")
    active = fields.Boolean("Active", default=True)
    display_create_info = fields.Char(compute="_get_create_record_info")
    display_modified_info = fields.Char(compute="_get_modify_record_info")
    company_id = fields.Many2one("res.company")
    rec_status = fields.Selection(
        [
            ("active", "Active"),
            ("disable", "Disable"),
        ],
        default="active",
        compute="_check_active_records",
        string="Status",
    )

    _sql_constraints = [
        (
            "name_unique",
            "unique(name)",
            "Container Facilities name should be unique.",
        ),
        (
            "code_unique",
            "unique(code)",
            "Container Facilities code should be unique.",
        ),
    ]

    def _get_create_record_info(self):
        """
        Assign create record log string to the appropriate field.
        :return: none
        """
        for rec in self:
            if rec.env.user.tz and rec.create_uid:
                tz_create_date = ResUsers.convert_datetime_to_user_timezone(
                    rec.env.user, rec.create_date
                )
                create_uid_name = rec.create_uid.name
                if tz_create_date:
                    rec.display_create_info = ResUsers.get_user_log_data(
                        rec, tz_create_date, create_uid_name
                    )
            else:
                rec.display_create_info = ""

    def _get_modify_record_info(self):
        """
        Assign update record log string to the appropriate field.
        :return: none
        """
        for rec in self:
            if rec.env.user.tz and rec.write_uid:
                tz_write_date = ResUsers.convert_datetime_to_user_timezone(
                    rec.env.user, rec.write_date
                )
                write_uid_name = rec.write_uid.name
                if tz_write_date:
                    rec.display_modified_info = ResUsers.get_user_log_data(
                        rec, tz_write_date, write_uid_name
                    )
            else:
                rec.display_modified_info = ""

    def _check_active_records(self):
        ContainerTypeEdi.check_active_records(self)
