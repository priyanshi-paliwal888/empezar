# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from .res_users import ResUsers
import re


class ContainerMaster(models.Model):

    _name = "container.master"
    _description = "Container"

    def get_years(self):
        """
        Generate a list of tuples containing years from 1950 to 3999.

        Returns:
            list: A list of tuples where each tuple contains a year as a string in the format (year, year).

        Example:
            >> get_years
            [('1950', '1950'), ('1951', '1951'), ..., ('3999', '3999')]
        """
        year_list = []
        for i in range(1950, 4000):
            year_list.append((str(i), str(i)))
        return year_list

    name = fields.Char(string="Container No.", size=11, translate=True)
    shipping_line_logo = fields.Binary(
        string="Shipping Line", related="shipping_line_id.logo"
    )
    shipping_line_id = fields.Many2one(
        "res.partner",
        string="Shipping Line",
        domain="[('is_shipping_line', '=', True)]",
    )
    type_size = fields.Many2one("container.type.data", string="Type/Size")
    production_month_year = fields.Char(
        "Production Month/Year", compute="_compute_date_field"
    )
    gross_wt = fields.Integer(string="Gross Wt. (KG)", size=12)
    tare_wt = fields.Integer(string="Tare Wt. (KG)", size=12)
    display_create_info = fields.Char(compute="_get_create_record_info")
    display_modified_info = fields.Char(compute="_get_modify_record_info")
    display_sources = fields.Char(string="Sources",readonly=True,compute="_compute_display_sources")
    month = fields.Selection(
        [
            ("01", "January"),
            ("02", "February"),
            ("03", "March"),
            ("04", "April"),
            ("05", "May"),
            ("06", "June"),
            ("07", "July"),
            ("08", "August"),
            ("09", "September"),
            ("10", "October"),
            ("11", "November"),
            ("12", "December"),
        ]
    )
    year = fields.Selection(get_years)
    company_id = fields.Many2one("res.company")
    is_import = fields.Boolean(string="Is Import", default=False)

    _sql_constraints = [
        ("name_unique", "unique (name)", "Container Name must be unique"),
    ]

    @api.depends("month", "year")
    def _compute_date_field(self):
        for record in self:
            if record.month and record.year:
                record.production_month_year = f"{record.month}/{record.year}"
            else:
                record.production_month_year = False

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

    @api.depends('is_import')
    def _compute_display_sources(self):
        """
        Assign Value while creating a record from an import file and Creating a custom Record
        """
        for record in self:
            if record.is_import:
                record.display_sources = 'Excel'
            else:
                record.display_sources = 'System'

    @api.constrains("gross_wt", "tare_wt")
    def _check_wt_validation(self):
        if self.gross_wt and self.tare_wt:
            if self.tare_wt > self.gross_wt:
                raise ValidationError(
                    _("Tare Weight cannot be greater than gross Weight")
                )
        if self.gross_wt == 0:
            raise ValidationError(_("Gross Weight cannot be 0"))
        if self.tare_wt == 0:
            raise ValidationError(_("Tare Weight cannot be 0"))

    @api.model
    def create(self, vals_list):
        """
        Assign custom field values while creating a record from an import file.
        :param vals_list:
        :return:
        """
        if self._context.get("import_file"):
            vals_list.update({"is_import": True})
        res = super().create(vals_list)
        return res

    @api.onchange('name')
    @api.constrains('name')
    def check_digit_validation_for_container(self):
        for record in self:
            if record.name:
                container_regex = r'^[A-Za-z]{4}[0-9]{7}$'
                if not re.match(container_regex, record.name):
                    raise ValidationError(_("Container Number is invalid."))

                char_to_num_dict = {
                    'A': 10, 'B': 12, 'C': 13, 'D': 14, 'E': 15, 'F': 16, 'G': 17, 'H': 18, 'I': 19,
                    'J': 20, 'K': 21, 'L': 23, 'M': 24, 'N': 25, 'O': 26, 'P': 27, 'Q': 28, 'R': 29,
                    'S': 30, 'T': 31, 'U': 32, 'V': 34, 'W': 35, 'X': 36, 'Y': 37, 'Z': 38
                }
                input_data = str(record.name).upper()
                sliced_input_data = input_data[:10]
                total_sum = sum(
                    (char_to_num_dict.get(char) if char_to_num_dict.get(char) else int(char)) * (2 ** index)
                    for index, char in enumerate(sliced_input_data)
                )
                rounded_division_result = (int(total_sum/11)) * 11
                remainder = total_sum - rounded_division_result
                new_digit = remainder % 10
                if new_digit != eval(record.name[-1]):
                    raise ValidationError(_("Container Number is invalid."))
