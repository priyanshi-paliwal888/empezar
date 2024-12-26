# -*- coding: utf-8 -*-

from odoo import fields, models, api
from .res_users import ResUsers
from odoo.exceptions import UserError, ValidationError

class ContainerTypeEdi(models.Model):

    _name = "container.type.edi"
    _description = "Container Type EDI"

    name = fields.Char(
        "Container Name", related="container_type_data_id.name", store=True
    )
    container_type_data_id = fields.Many2one(
        "container.type.data", string="Container Name"
    )
    type_group_code = fields.Char(
        "Container Type Group Code",
        related="container_type_data_id.company_size_type_code",
        store=True,
    )
    edi_code = fields.Char("EDI Code", size=10, required=True, translate=True)
    partner_id = fields.Many2one("res.partner", string="Partner", ondelete="cascade")
    display_create_info = fields.Char(compute="_get_create_record_info")
    display_modified_info = fields.Char(compute="_get_modify_record_info")
    company_id = fields.Many2one("res.company")
    active = fields.Boolean("Status", default=True)
    rec_status = fields.Selection(
        [
            ("active", "Active"),
            ("disable", "Disable"),
        ],
        default="active",
        compute="check_active_records",
        string="Status",
    )

    _sql_constraints = [
        ("edi_code_uniq", "unique (edi_code)", "EDI with the same code already exists.")
    ]

    def check_active_records(self):
        """
        This method iterates through all records in the current recordset
        and updates their `rec_status` field based on the value of the
        `active` field.

        - If a record's `active` field is True, the `rec_status` field is set to "active".
        - If a record's `active` field is False, the `rec_status` field is set to "disabled".

        Args:
            self (Recordset): The current recordset of the model.
        """
        for rec in self:
            if rec.active:
                rec.rec_status = "active"
            else:
                rec.rec_status = "disable"

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
            if self.env.user.tz and rec.write_uid:
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

    @api.onchange('container_type_data_id')
    def _onchange_container_type_data_id(self):
        """
        Test that a container_type_data_id is not active raises a ValidationError.
        """
        if self.container_type_data_id and not self.container_type_data_id.active:
            raise ValidationError('Please Select Active Container Name.')