# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from .contrainer_type_edi import ContainerTypeEdi
from .res_users import ResUsers


class ResCompany(models.Model):
    _inherit = "res.company"

    location_type = fields.Selection(
        [("cfs", "CFS"), ("terminal", "Terminal"), ("empty_yard", "Empty Yard")],
        string="Location Type",
    )
    location_code = fields.Char(string="Location Code", size=7)
    port = fields.Many2one("master.port.data", string="Port")
    capacity = fields.Char(string="Capacity (TEUs)", size=9)
    rec_status = fields.Selection(
        [
            ("active", "Active"),
            ("disable", "Disable"),
        ],
        default="active",
        compute="_check_active_records",
        string="Status",
    )
    mode_ids = fields.Many2many("mode.options", string="Mode")
    mode = fields.Selection([("truck", "Truck"), ("rail", "Rail")], string="Mode")
    laden_status_ids = fields.Many2many("laden.status.options", string="Laden Status")
    laden_status = fields.Selection(
        [("laden", "CFS"), ("empty", "Terminal")], string="Laden Status"
    )
    operations_ids = fields.Many2many("operations.options", string="Operations")
    operations = fields.Selection(
        [("gate_operations", "Gate Operations"), ("repair", "Repair")],
        string="operations",
    )
    display_create_info = fields.Char(compute="_get_create_record_info")
    display_modified_info = fields.Char(compute="_get_modify_record_info")
    movement_move_in_settings_ids = fields.One2many(
        "movement.setting",
        "company_id",
        string="Movement Move In Settings",
        domain=[("movement_type", "=", "move_in")],
    )
    movement_move_out_settings_ids = fields.One2many(
        "movement.setting",
        "company_id",
        string="Movement Move Out Settings",
        domain=[("movement_type", "=", "move_out")],
    )
    shipping_line_mapping_ids = fields.One2many(
        "location.shipping.line.mapping", "company_id", string="Shipping Line Mapping"
    )
    invoice_setting_ids = fields.One2many(
        "location.invoice.setting", "company_id", string="Invoice Setting"
    )
    port_code = fields.Char(string="Port Code", related="port.port_code")
    port_name = fields.Char(string="Port Code", related="port.port_name")
    port_iso_code = fields.Char(string="Port Code", related="port.country_iso_code")
    port_iso_with_code = fields.Char(string="Port Code", related="port.combined_iso_and_port")

    @api.model
    def default_get(self, fields_list):
        """
        Set default country from main company when user create a location.
        Set parent id to main company when user create location.
        :param fields_list
        :return:
        """
        res = super().default_get(fields_list)
        if self._context.get("is_res_company_location_view"):
            main_company = self.env.ref("base.main_company")
            res["country_id"] = (
                main_company.country_id.id if main_company.country_id else False
            )
            res["parent_id"] = main_company.id if main_company else False
        return res

    def _check_active_records(self):
        ContainerTypeEdi.check_active_records(self)

    @api.constrains("location_code", "name")
    def _check_location_code_validations(self):
        existing_companies = self.search([("id", "!=", self.id)])
        if self.name:
            names = existing_companies.mapped("name")
            if self.name in names:
                raise ValidationError(_("Location with the same name already exists."))
        if self.location_code:
            existing_location_codes = existing_companies.mapped("location_code")
            if self.location_code in existing_location_codes:
                raise ValidationError(
                    _("Location with the same Location Code already exists.")
                )

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

    @api.onchange("port")
    def onchange_port(self):
        if self.port:
            self.latitude = self.port.latitude
            self.longitude = self.port.longitude

    @api.constrains('capacity')
    @api.onchange('capacity')
    def _capacity_numeric_validation(self):
        """
       This method validates the Capacity entered by the user.
       Raises:
           ValidationError:
               - If the Capacity contains non-numeric characters.
       """
        for rec in self:
            if rec.capacity:
                if not rec.capacity.isdigit():
                    raise ValidationError("The Capacity must contain only numeric values.")
