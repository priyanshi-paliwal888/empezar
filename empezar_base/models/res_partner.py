# -*- coding: utf-8 -*-

import base64
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import file_open
from .res_users import ResUsers
from odoo.fields import Command


class ResPartner(models.Model):

    _inherit = "res.partner"

    @api.model
    def _default_image(self):
        return base64.b64encode(
            file_open(
                "empezar_base/static/src/img/default_shipping_line_logo.png", "rb"
            ).read()
        )

    # shipping line fields
    shipping_line_name = fields.Char("Shipping Line Name", size=56, translate=True)
    shipping_line_code = fields.Char(
        size=6, string="Shipping Line Code", translate=True
    )
    applied_for_interchange = fields.Selection(
        [
            ("yes", "Yes"),
            ("no", "No"),
        ],
        default="no",
    )
    logo = fields.Binary(string="Shipping Line Logo", default=_default_image)
    active = fields.Boolean(default=True)
    line_status = fields.Selection(
        [("active", "Active"), ("inactive", "Disable")],
        "Status",
        default="active",
        compute="_check_line_status",
    )
    is_shipping_line = fields.Boolean("Is Shipping Line", default=False)
    container_type_edi_ids = fields.One2many(
        "container.type.edi",
        "partner_id",
        string="Container Type EDI",
        domain=["|", ("active", "=", True), ("active", "=", False)],
        context={"active_test": False},
    )
    shipping_line_transporters_ids = fields.One2many(
        "shipping.line.transporters",
        "partner_id",
        string="Transporters",
        domain=["|", ("active", "=", True), ("active", "=", False)],
        context={"active_test": False},
    )
    display_create_info = fields.Char(compute="_get_create_record_info")
    display_modified_info = fields.Char(compute="_get_modify_record_info")
    gst_state = fields.Char(string="State")

    # parties fields
    party_name = fields.Char("Party Name", translate=True)
    is_this_billed_to_party = fields.Selection(
        [
            ("yes", "Yes"),
            ("no", "No"),
        ],
        default="no",
        string="Is this a Billed To Party",
    )
    is_gst_applicable = fields.Selection(
        [
            ("yes", "Yes"),
            ("no", "No"),
        ],
        default="no",
        string="GST Applicable",
    )
    parties_type_ids = fields.Many2many(
        "cms.parties.type", "cms_parties_type_rel", string="Type", required=True
    )
    gst_no = fields.Char(string="GST No.", size=15, translate=True)
    is_cms_parties = fields.Boolean("Is CMS Parties", default=False)
    parties_gst_invoice_line_ids = fields.One2many(
        "gst.details",
        "partner_id",
        string="GST Invoice Lines",
        context={"active_test": False},
    )
    tax_payer_type = fields.Char("TAXPAYER TYPE")
    nature_of_business = fields.Char("NATURE OF BUSINESS")
    state_jurisdiction = fields.Char(string="STATE JURISDICTION")
    additional_place_of_business = fields.Char("ADDITIONAL PLACE OF BUSINESS 1")
    nature_additional_place_of_business = fields.Char(
        "NATURE OF ADDITIONAL PLACE OF BUSINESS 1"
    )
    additional_place_of_business_2 = fields.Char("ADDITIONAL PLACE OF BUSINESS 2")
    nature_additional_place_of_business_2 = fields.Char(
        "NATURE OF ADDITIONAL PLACE OF BUSINESS 2"
    )
    last_update = fields.Char("LAST UPDATE ON")
    parties_gst_api_response = fields.Text("API Response")

    _sql_constraints = [
        (
            "shipping_line_name_uniq",
            "unique (shipping_line_name)",
            "Shipping Line with the same name already exists.",
        ),
        (
            "shipping_line_code_uniq",
            "unique (shipping_line_code)",
            "Shipping Line with the same Shipping LineCode already exists.",
        ),
        # (
        #     "gst_no_uniq",
        #     "unique (gst_no)",
        #     "This GST number already exists in another party.",
        # ),
        ("party_name_uniq", "unique (party_name)", "Party Name already exists."),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        """
        Assign mandatory field values while create a record from shipping lines.
        :param vals_list:
        :return:
        """
        if self._context.get("is_shipping_view"):
            shipping_line_tag_id = self.env.ref(
                "empezar_base.res_partner_shipping_tag_1"
            ).id
            for vals in vals_list:
                vals.update(
                    {
                        "is_shipping_line": True,
                        "name": vals["shipping_line_name"],
                        "category_id": [shipping_line_tag_id],
                    }
                )
        if self._context.get("is_cms_parties_view"):
            cms_parties_tag_id = self.env.ref(
                "empezar_base.res_partner_cms_parties_tag_1"
            ).id
            for vals in vals_list:
                vals.update(
                    {
                        "is_cms_parties": True,
                        "name": vals["party_name"],
                        "category_id": [cms_parties_tag_id],
                    }
                )
        res = super().create(vals_list)
        return res

    def add_gst_line(self):
        """
        Opens the GST form wizard for adding a new GST line.

        Returns:
            A dictionary representing an action that opens the GST form wizard.
        """
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "empezar_base.gst_details_form_action"
        )
        action["name"] = action["name"] + " - " + self.name
        return action

    def write(self, vals):
        """
        update the name fields while update the shipping line name from shipping line view.
        :param vals:
        :return:
        """
        if self._context.get("is_shipping_view") and vals.get("shipping_line_name"):
            vals.update({"name": vals["shipping_line_name"]})
        if self._context.get("is_cms_parties_view") and vals.get("party_name"):
            vals.update({"name": vals["party_name"]})
        res = super().write(vals)
        return res

    def _check_line_status(self):
        """
        update the line status based on the record is active or not.
        :return:
        """
        for rec in self:
            if rec.active:
                rec.line_status = "active"
            else:
                rec.line_status = "inactive"

    @api.onchange("logo")
    @api.constrains("logo")
    def _check_shipping_line_logo_validation(self):
        """
        This method validates the uploaded shipping logo:

        **Raises:**
            ValidationError: If the uploaded logo size exceeds 1MB.
        """
        if self.logo and len(self.logo) > 1048576:  # 1MB in bytes
            raise ValidationError("Image size cannot exceed 1MB.")

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

    @api.constrains("is_gst_applicable")
    def check_gst_applicable_details(self):
        """
        validate the gst number and update the data as per the api response.
        :return:
        """
        if self.is_gst_applicable == "yes":
            fields_to_check = [
                self.tax_payer_type,
                self.nature_of_business,
                self.state_jurisdiction,
                self.additional_place_of_business,
                self.nature_additional_place_of_business,
                self.additional_place_of_business_2,
                self.nature_additional_place_of_business_2,
                self.last_update
            ]
            if all(not field for field in fields_to_check):
                raise ValidationError(_('Please Add Valid GST Numbers'))
        if self.is_gst_applicable == "yes" and not self.parties_gst_invoice_line_ids:
            self.with_context(is_cms_parties_view=True).parties_gst_invoice_line_ids = [Command.create({'gst_no': self.gst_no,
                                                                 'tax_payer_type': self.tax_payer_type,
                                                                 'state': self.gst_state,
                                                                 'status': 'Active',
                                                                 'nature_of_business': self.nature_of_business,
                                                                 'state_jurisdiction': self.state_jurisdiction,
                                                                 'additional_place_of_business': self.additional_place_of_business,
                                                                 'nature_additional_place_of_business': self.nature_additional_place_of_business,
                                                                 'additional_place_of_business_2': self.additional_place_of_business_2,
                                                                 'nature_additional_place_of_business_2': self.nature_additional_place_of_business_2,
                                                                 'last_update': self.last_update,
                                                                 'gst_api_response': self.parties_gst_api_response})]

        if self.is_gst_applicable == "no" and self.parties_gst_invoice_line_ids:
            raise ValidationError(
                _("Not allowed to change status once gst details has been added in Gst Applicable Field.")
            )

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

    @api.constrains('gst_no')
    def _check_gst_no_unique(self):
        for record in self:
            if record.gst_no:
                existing_party = self.search([('gst_no', '=', record.gst_no), ('id', '!=', record.id)], limit=1)
                if existing_party:
                    raise ValidationError(f"GST No. {record.gst_no} is set for {existing_party.party_name}. Please enter a different GST No.")
