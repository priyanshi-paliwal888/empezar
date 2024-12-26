# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from ...empezar_base.models.res_users import ResUsers
import re


class ContainerInventory(models.Model):

    _name = "container.inventory"
    _description = "Container Inventory"
    _rec_name = "name"

    def get_hours(self):
        hour_list = []
        for i in range(0, 24):
            hour_list.append((str(i), str(i)))
        return hour_list

    def get_minutes(self):
        minutes_list = []
        for i in range(0, 60):
            minutes_list.append((str(i), str(i)))
        return minutes_list

    move_in_date = fields.Date(string="In Date")
    move_out_date = fields.Date(string="Out Date")
    active = fields.Boolean(String="Active", default=True)
    status = fields.Selection([
        ('ae', 'AE'),
        ('aa', 'AA'),
        ('ar', 'AR'),
        ('av', 'AV'),
        ('dav', 'DAV')
    ], string="Status")
    grade = fields.Selection([
        ('a', 'A'),
        ('b', 'B'),
        ('c', 'C'),
    ], string="Grade")
    container_master_id = fields.Many2one('container.master', string="Container master", ondelete='cascade', required=True)
    damage_condition = fields.Many2one('damage.condition', string="Damage Condition")
    estimate_date = fields.Date(string="Estimate Date")
    estimate_amount = fields.Float(string="Estimate Amount")
    approval_date = fields.Date(string="Approval Date")
    approved_amount = fields.Float(string="Approved Amount")
    repair_date = fields.Date(string="Repair Date")
    remarks = fields.Text(string="Remarks")
    location_id = fields.Many2one('res.company', domain=[('parent_id', '!=', False)])
    hour = fields.Selection(get_hours)
    minutes = fields.Selection(get_minutes)
    out_hour = fields.Selection(get_hours)
    out_minutes = fields.Selection(get_minutes)
    name = fields.Char(string="Container No.", size=11, translate=True, required=True)
    hold_release_status = fields.Selection(
        [
            ("hold", "Hold"),
            ("release", "Release")
        ], string="Hold/Release Status"
    )
    display_create_info = fields.Char(compute="_get_create_record_info")
    display_modified_info = fields.Char(compute="_get_modify_record_info")
    display_sources = fields.Char(string="Sources", readonly=True,
                                  compute="_compute_display_sources")
    company_id = fields.Many2one(
        "res.company",
        required=True,
        readonly=True,
        default=lambda self: self.env.company,
    )
    is_import = fields.Boolean(string="Is Import", default=False)

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
                    (char_to_num_dict.get(char) if char_to_num_dict.get(char) else int(char)) * (
                                2 ** index)
                    for index, char in enumerate(sliced_input_data)
                )
                rounded_division_result = (int(total_sum / 11)) * 11
                remainder = total_sum - rounded_division_result
                new_digit = remainder % 10
                if new_digit != eval(record.name[-1]):
                    raise ValidationError(_("Container Number is invalid."))

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
                    (char_to_num_dict.get(char) if char_to_num_dict.get(char) else int(char)) * (
                                2 ** index)
                    for index, char in enumerate(sliced_input_data)
                )
                rounded_division_result = (int(total_sum / 11)) * 11
                remainder = total_sum - rounded_division_result
                new_digit = remainder % 10
                if new_digit != eval(record.name[-1]):
                    raise ValidationError(_("Container Number is invalid."))
