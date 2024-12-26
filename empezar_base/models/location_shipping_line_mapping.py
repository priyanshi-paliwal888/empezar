# -*- coding: utf-8 -*-

import re
from odoo import fields, models, _, api
from odoo.exceptions import ValidationError
from .contrainer_type_edi import ContainerTypeEdi
from .res_users import ResUsers


class LocationShippingLineMapping(models.Model):

    _name = "location.shipping.line.mapping"
    _description = "Shipping Line Mapping"
    _rec_name = "shipping_line_id"

    shipping_line_id = fields.Many2one("res.partner", string="Shipping Line")
    shipping_line_logo = fields.Binary(
        string="Shipping Line", related="shipping_line_id.logo"
    )
    company_id = fields.Many2one("res.company", string="Company", ondelete="cascade")
    active = fields.Boolean(string="Active", default=True)
    rec_status = fields.Selection(
        [
            ("active", "Active"),
            ("disable", "Disable"),
        ],
        default="active",
        compute="_check_active_records",
        string="Status",
    )
    display_create_info = fields.Char(compute="_get_create_record_info")
    display_modified_info = fields.Char(compute="_get_modify_record_info")

    # location setting fields.
    gate_pass_ids = fields.Many2many("gate.pass.options", string="Gate Pass")
    gate_pass = fields.Char(string="Gate Pass", compute="_get_gate_pass_values")
    refer_container = fields.Selection([("yes", "Yes"), ("no", "No")], default="no")
    capacity = fields.Char(string="Capacity (TEUs)", size=9)

    # seal setting fields
    seal_threshold = fields.Char(string="Seal Threshold", size=5)
    from_email = fields.Char(string="From Email")
    to_email = fields.Char(string="To Email")
    cc_email = fields.Char(string="CC Email")
    email_sent_on = fields.Datetime("Email Sent on")

    @api.model
    def write(self, vals):
        if 'active' in vals and not vals.get('active', True):
            for record in self:
                container_count = self.env['container.master'].search_count(
                    [('shipping_line_id', '=', record.shipping_line_id.id)]
                )
                if container_count > 0:
                    raise ValidationError(
                        _("Cannot deactivate this shipping line as it is used in container master records.")
                    )

        res = super(LocationShippingLineMapping, self).write(vals)

        if 'active' in vals and self._context.get('is_res_company_location_view'):
            self.company_id.check_shipping_line_capacity()
        return res

    @api.onchange('seal_threshold')
    def onchange_seal_threshold(self):
        for record in self:
            if record.seal_threshold and not record.seal_threshold.isdigit():
                raise ValidationError("The Seal Threshold must contain only numeric values.")

    @api.depends("gate_pass_ids")
    def _get_gate_pass_values(self):
        value = []
        if self.gate_pass_ids:
            if (
                self.env.ref("empezar_base.gate_pass_move_in").id
                in self.gate_pass_ids.ids
            ):
                value.append("Move In")
            if (
                self.env.ref("empezar_base.gate_pass_move_out").id
                in self.gate_pass_ids.ids
            ):
                value.append("Move Out")
            self.gate_pass = ", ".join(value) if value else False
        else:
            self.gate_pass = False

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

    def _get_domain(self):
        get_transporter_id = self.env.ref("empezar_base.cms_parties_type_6").id
        domain = (
            self.env["res.partner"]
            .search([])
            .filtered(lambda record: get_transporter_id in record.parties_type_ids.ids)
        )
        return [("id", "in", domain.ids)]

    # Repair setting fields
    repair = fields.Selection(
        [("yes", "Yes"), ("no", "No")], default="no", string="Repair Estimates"
    )
    repair_vendor_is_same_company = fields.Selection(
        [("yes", "Yes"), ("no", "No")],
        default="yes",
        string="Repair Vendor is same as Company",
    )
    repair_vendor_name = fields.Many2one(
        "res.partner", string="Repair Vendor Name", domain=_get_domain
    )
    # repair_vendor_name = fields.Char(string="Repair Vendor Name")
    depot_name = fields.Char(string="Depot Name", size=72)
    depot_code = fields.Char(string="Depot Code", size=20)
    repair_vendor_code = fields.Char(string="Repair Vendor Code", size=20)
    labour_rate = fields.Char(string="Labour Rate", size=4)
    ftp_location = fields.Char(string="FTP Location")
    ftp_username = fields.Char(string="FTP Username")
    ftp_password = fields.Char(string="FTP Password")
    port_number = fields.Integer(string="Port Number")
    secure_connection = fields.Selection(
        [("yes", "Yes"), ("no", "No")], string="Secure Connection"
    )
    ftp_folder_name = fields.Char(string="FTP Folder Name")
    folder_name_westim = fields.Char(string="Folder Name - WESTIM")
    folder_name_destim = fields.Char(string="Folder Name - DESTIM")
    folder_name_destim_response = fields.Char(string="Folder Name - DESTIM Response")
    folder_name_before_images = fields.Char(string="Folder Name - Before Images")
    folder_name_after_images = fields.Char(string="Folder Name - After Images")

    # Remarks
    remarks = fields.Char(string="Remarks", size=128)



    def _check_active_records(self):
        ContainerTypeEdi.check_active_records(self)

    def validate_email(self, email):
        email_regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
        if email and not re.fullmatch(email_regex, email):
            raise ValidationError(
                _("Invalid email address. Please enter a correct email address.")
            )

    @api.onchange("from_email", "to_email", "cc_email")
    @api.constrains("from_email", "to_email", "cc_email")
    def check_emails(self):
        for record in self:
            record.validate_email(record.from_email)
            record.validate_email(record.to_email)
            record.validate_email(record.cc_email)

    @api.constrains("shipping_line_id")
    def check_shipping_line_validation(self):
        existing_shipping_line = (
            self.search(
                [("company_id", "=", self.company_id.id), ("id", "!=", self.id)]
            )
            .mapped("shipping_line_id")
            .ids
        )
        if self.shipping_line_id and self.shipping_line_id.id in existing_shipping_line:
            raise ValidationError(_("Shipping Line is already mapped"))

    @api.constrains('labour_rate')
    @api.onchange('labour_rate')
    def _labour_rate_numeric_validation(self):
        """
       This method validates the Labour Rate entered by the user.
       Raises:
           ValidationError:
               - If the Labour Rate contains non-numeric characters.
       """
        for rec in self:
            if rec.labour_rate:
                if not rec.labour_rate.isdigit():
                    raise ValidationError("The Labour Rate must contain only numeric values.")

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

