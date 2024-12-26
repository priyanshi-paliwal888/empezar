# -*- coding: utf-8 -*-

from odoo import fields, models, _, api
from odoo.exceptions import ValidationError
from .contrainer_type_edi import ContainerTypeEdi
from .res_users import ResUsers


class LocationInvoiceSetting(models.Model):

    _name = "location.invoice.setting"
    _description = "Location Invoice Setting"

    inv_applicable_at_location_ids = fields.Many2many(
        "invoice.applicable.options", string="Invoice Applicable at this Location"
    )
    inv_applicable_at_location = fields.Char(
        string="Invoice Type", compute="_get_inv_applicable_values"
    )
    company_id = fields.Many2one("res.company", string="Company", ondelete="cascade")
    inv_shipping_line_id = fields.Many2one("res.partner", string="Shipping Line")
    inv_shipping_line_domain = fields.Many2many(
        "res.partner", compute="_compute_inv_shipping_line_domain"
    )
    inv_shipping_line_logo = fields.Binary(
        string="Shipping Line", related="inv_shipping_line_id.logo"
    )
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

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        payment_mode_cash_id = self.env.ref("empezar_base.payment_mode_cash").id
        if payment_mode_cash_id:
            res["payment_mode_ids"] = [payment_mode_cash_id]
        return res

    @api.depends("inv_applicable_at_location_ids")
    def _get_inv_applicable_values(self):
        for record in self:
            value = []
            if record.inv_applicable_at_location_ids:
                if (
                        self.env.ref("empezar_base.inv_applicable_lift_off").id
                        in record.inv_applicable_at_location_ids.ids
                ):
                    value.append("Lift Off")
                if (
                        self.env.ref("empezar_base.inv_applicable_lift_on").id
                        in record.inv_applicable_at_location_ids.ids
                ):
                    value.append("Lift On")
                if (
                        self.env.ref("empezar_base.inv_applicable_others").id
                        in record.inv_applicable_at_location_ids.ids
                ):
                    value.append("Others")
                record.inv_applicable_at_location = ", ".join(value) if value else False
            else:
                record.inv_applicable_at_location = False

    @api.depends("inv_shipping_line_id")
    def _compute_inv_shipping_line_domain(self):
        for record in self:
            if record.company_id:
                shipping_line_ids = record.company_id.shipping_line_mapping_ids.mapped(
                    "shipping_line_id"
                ).ids
                record.inv_shipping_line_domain = shipping_line_ids
            else:
                record.inv_shipping_line_domain = (
                    self.env["shipping.line"].search([]).ids
                )

    def _check_active_records(self):
        ContainerTypeEdi.check_active_records(self)

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

    # company details
    company_name_in_inv = fields.Selection(
        [("same_as_company", "Same as Company"), ("others", "Others")],
        string="Company Name on Invoice",
        default="same_as_company",
    )
    company_name = fields.Char(strin="Company Name", size=72)
    country_id = fields.Many2one("res.country", string="Country")
    address_line_1 = fields.Char(string="Address Line 1", size=128)
    address_line_2 = fields.Char(string="Address Line 2", size=128)
    city = fields.Char(string="City", size=72)
    state_id = fields.Many2one(
        "res.country.state", string="State", domain="[('country_id', '=', country_id)]"
    )
    pincode = fields.Char(string="Pincode", size=6)

    # GST Details
    gst_no = fields.Selection(
        [("same_as_cmp", "Same as Company"), ("others", "Others")],
        string="GST No./CIN on Invoice",
    )
    gst_number = fields.Char(string="GST No.", size=15)
    cin_no = fields.Char(string="CIN", size=21)

    e_invoice_applicable = fields.Selection(
        [("yes", "Yes"), ("no", "No")], default="yes", string="E-Invoicing Applicable"
    )
    payment_mode_ids = fields.Many2many("payment.mode.options", string="Payment Mode")
    payment_mode = fields.Char(
        string="Payment Mode", compute="_get_payment_mode_values"
    )

    @api.onchange("gst_no")
    def onchange_gst_no(self):
        if self.gst_no == "same_as_cmp":
            main_company = self.env["res.company"].search(
                [("parent_id", "=", False)], limit=1
            )
            if main_company:
                self.cin_no = main_company.cin
        elif self.cin_no:
            self.cin_no = False

    @api.onchange("company_name_in_inv")
    def onchange_company_name_in_inv(self):
        if self.company_name_in_inv == "others":
            self.country_id = False
            self.address_line_1 = False
            self.address_line_2 = False
            self.city = False
            self.state_id = False
            self.pincode = False
        elif self.company_name_in_inv == "same_as_company":
            main_company = self.env["res.company"].search(
                [("parent_id", "=", False)], limit=1
            )
            if main_company:
                self.country_id = (
                    main_company.country_id.id if main_company.country_id else False
                )
                self.state_id = (
                    main_company.state_id.id if main_company.state_id else False
                )
            if self.company_id:
                self.address_line_1 = self.company_id.street
                self.address_line_2 = self.company_id.street2
                self.city = self.company_id.city
                self.pincode = self.company_id.zip

    @api.constrains("inv_shipping_line_id")
    def check_shipping_line_validation(self):
        for record in self:
            existing_shipping_line = (
                self.search(
                    [("company_id", "=", record.company_id.id), ("id", "!=", record.id)]
                )
                .mapped("inv_shipping_line_id")
                .ids
            )
            if (
                record.inv_shipping_line_id
                and record.inv_shipping_line_id.id in existing_shipping_line
            ):
                raise ValidationError(_("Shipping Line is already mapped"))

    @api.depends("payment_mode_ids")
    def _get_payment_mode_values(self):
        for record in self:
            value = []
            if record.payment_mode_ids:
                if (
                        self.env.ref("empezar_base.payment_mode_cash").id
                        in record.payment_mode_ids.ids
                ):
                    value.append("Cash")
                if (
                        self.env.ref("empezar_base.payment_mode_online").id
                        in record.payment_mode_ids.ids
                ):
                    value.append("Online")
                record.payment_mode = ", ".join(value) if value else False
            else:
                record.payment_mode = False

    @api.constrains('pincode')
    @api.onchange('pincode')
    def _check_pincode_validation(self):
        """
        This method validates the pincode entered by the user.
        Raises:
            ValidationError:
                - If the pincode contains non-numeric characters.
        """
        for rec in self:
            if rec.pincode:
                if not rec.pincode.isdigit():
                    raise ValidationError("The Pincode must contain only numeric values.")
