# -*- coding: utf-8 -*-

import re
from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
from pytz import timezone as pytz


class ResUsers(models.Model):

    _inherit = "res.users"

    user_status = fields.Selection(
        [("active", "Active"), ("inactive", "In Active")],
        "Status",
        default="active",
        compute="_check_user_status",
    )
    display_create_info = fields.Char(compute="_get_create_record_info")
    display_modified_info = fields.Char(compute="_get_modify_record_info")
    name = fields.Char(
        related="partner_id.name", inherited=True, readonly=False, size=56
    )
    company_id = fields.Many2one(
        'res.company',
        string='Default Location',
        domain="[('parent_id', '!=', False)]"
    )

    @api.constrains("email")
    @api.onchange("email")
    def is_valid_email(self):
        """
        This function checks if the provided email address is valid using a regular expression.

        Returns:
            True if the email is valid, False otherwise.
        """
        email_regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
        if self.email and not bool(re.fullmatch(email_regex, self.email)):
            raise ValidationError(
                _("Invalid email address. Please enter correct email address.")
            )
        if self.email and len(self.email) > 56:
            raise ValidationError(_("Email cannot exceed 56 characters"))

    @api.constrains("mobile")
    def _check_contact_no(self):
        if self.mobile:
            if not self.mobile.isdigit():
                raise ValidationError(
                    _("Invalid contact number. Only Numeric values allow.")
                )
            if len(self.mobile) > 10:
                raise ValidationError(
                    _("Invalid contact number. Maximum 10 digits allow.")
                )
            get_mobile = (
                self.env["res.users"]
                .search([("active", "=", True), ("id", "!=", self.id)])
                .mapped("mobile")
            )
            if self.mobile in get_mobile:
                raise ValidationError(_("Contact number already exists !"))

    @api.constrains("login")
    @api.onchange("login")
    def is_valid_login(self):
        """
        This function checks if the provided login is valid or not.
        """
        if self.login and len(self.login) > 56:
            raise ValidationError(_("Username cannot exceed 56 characters"))

    def _check_user_status(self):
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
                rec.user_status = "active"
            else:
                rec.user_status = "inactive"

    def convert_datetime_to_user_timezone(self, datetime):
        """
        Converts a datetime object from UTC to the user's preferred timezone.
        :return: datetime.datetime or False:
        """
        date_utc = datetime
        # get users timezone
        user_time_zone = pytz(self.tz)
        # Convert from UTC to user's timezone
        user_tz = date_utc.astimezone(user_time_zone)
        if user_tz:
            return user_tz
        return False

    def _get_create_record_info(self):
        """
        Assign create record log string to the appropriate field.
        :return: none
        """
        for rec in self:
            if rec.tz and rec.create_uid:
                tz_create_date = rec.convert_datetime_to_user_timezone(rec.create_date)
                create_uid_name = rec.create_uid.name
                if tz_create_date:
                    rec.display_create_info = self.get_user_log_data(
                        tz_create_date, create_uid_name
                    )
            else:
                rec.display_create_info = ""

    def _get_modify_record_info(self):
        """
        Assign update record log string to the appropriate field.
        :return: none
        """
        for rec in self:
            if rec.tz and rec.write_uid:
                tz_write_date = rec.convert_datetime_to_user_timezone(rec.write_date)
                write_uid_name = rec.write_uid.name
                if tz_write_date:
                    rec.display_modified_info = self.get_user_log_data(
                        tz_write_date, write_uid_name
                    )
            else:
                rec.display_modified_info = ""

    def get_user_log_data(self, date, name):
        """
        this method return a user log string.
        """
        rec_date = date.strftime("%d/%m/%Y")
        rec_time = date.strftime("%I:%M %p")
        return name + " " + "|" + " " + rec_date + " " + rec_time
