# -*- coding: utf-8 -*-

import re
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from countryinfo import CountryInfo


class ResCompany(models.Model):
    _inherit = "res.company"

    name = fields.Char(
        "Company Name", index=True, tracking=True, required=True, translate=True, size=128
    )
    country_id = fields.Many2one(
        "res.country", index=True, tracking=True, required=True
    )
    street = fields.Char(index=True, tracking=True)
    street2 = fields.Char(index=True, tracking=True)
    city = fields.Char(index=True, tracking=True)
    zip = fields.Char(index=True, tracking=True, size=6)
    email = fields.Char(string="Email", tracking=True)
    escalation_email = fields.Char(string="Escalation Email ID(s)", tracking=True)
    phone = fields.Char(string="Phone", size=10, tracking=True)
    currency_id = fields.Many2one("res.currency", tracking=True)
    phone_country_code = fields.Char(string="Phone Code")
    state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="State",
        domain="[('country_id', '=', country_id)]",
        tracking=True,
    )
    pan = fields.Char("PAN", index=True, tracking=True)
    cin = fields.Char("CIN", index=True, tracking=True)
    report_no_of_days = fields.Integer(
        "View Report (No of days)", index=True, tracking=True
    )
    primary_color = fields.Char("Primary Color", tracking=True)
    date_format = fields.Selection(
        [
            ("DD/MM/YYYY", "DD/MM/YYYY"),
            ("YYYY/MM/DD", "YYYY/MM/DD"),
            ("MM/DD/YYYY", "MM/DD/YYYY"),
        ],
        string="Date Format",
        default="DD/MM/YYYY",
        index=True,
        tracking=True,
    )
    gst_invoice_line_ids = fields.One2many(
        "gst.details",
        "company_id",
        string="Edit GST- Empezar Global Marine Service Pvt Ltd",
        context={"active_test": False},
    )
    gst_integration_line_ids = fields.One2many(
        "gst.integration", "company_id", string="Integration"
    )
    e_invoice_applicable = fields.Selection(
        [("yes", "Yes"), ("no", "No")],
        string="E-Invoice Applicable",
        index=True,
        tracking=True,
    )

    client_id = fields.Char(string="Client ID", index=True, tracking=True)
    client_secret = fields.Char(string="Client Secret", index=True, tracking=True)
    is_country_india = fields.Boolean(
        string="Is India ?", default=False, compute="_check_is_country_india"
    )
    latitude = fields.Char(string="Latitude")
    longitude = fields.Char(string="Longitude")
    gst_no = fields.Char(string="GST Number")
    remarks = fields.Char(string="Remarks", size=128)
    _sql_constraints = [
        ('location_name_uniq', 'unique (name)', 'Location with the same name already exists')
    ]

    @api.onchange('country_id')
    def _onchange_country_id(self):
        if self.country_id:
            country = self.country_id
            country_info = CountryInfo(country.name)
            try:
                if country_info:
                    calling_codes = country_info.calling_codes()
                    if calling_codes:
                        self.phone_country_code = '+' + calling_codes[0]
                    else:
                        self.phone_country_code = ''
                else:
                    self.phone_country_code = ''
            except Exception as e:
                self.phone_country_code = ''

    @api.model
    def update_container_status_dates(self):
        ContainerStatus = self.env['update.container.status']
        records_to_update = ContainerStatus.search([('uploaded_on', '!=', False)])

        for record in records_to_update:
            if record.uploaded_on:
                current_date = record.uploaded_on
                formatted_date = self._format_date(current_date, self.date_format)
                record.write({'uploaded_on': formatted_date})

    def _format_date(self, date, format):
        if not date or not format:
            return date

        date_obj = fields.Datetime.from_string(date)

        if format == 'dd/mm/yyyy':
            return date_obj.strftime('%d/%m/%Y %H:%M:%S')
        elif format == 'mm/dd/yyyy':
            return date_obj.strftime('%m/%d/%Y %H:%M:%S')
        elif format == 'yyyy/mm/dd':
            return date_obj.strftime('%Y/%m/%d %H:%M:%S')
        else:
            return date

    def _valid_field_parameter(self, field, name):
        """Return whether the given parameter name is valid for the field."""
        return name == "tracking" or super()._valid_field_parameter(field, name)

    @api.onchange("country_id")
    def _check_is_country_india(self):
        """
        This method is triggered whenever the `country_id` field is changed in the form view.

        It checks if the selected country is India (code: 'IN').
        If it is, it sets the `is_country_india` field to `True`.

        Args:
            self (odoo.models.BaseModel): The current record of the model.

        Returns:
            None
        """
        country_id = self.env["res.country"].search([("code", "=", "IN")], limit=1)
        for rec in self:
            if rec.country_id.id == country_id.id:
                rec.is_country_india = True
            else:
                rec.is_country_india = False

    @api.constrains("report_no_of_days")
    @api.onchange("report_no_of_days")
    def _check_validation(self):
        """
        This method is triggered whenever the `report_no_of_days` field is changed in the form view.

        It validates that the entered number of days is within the allowed range (0 to 9999).
        If the value is outside the range, it raises a validation error with a user-friendly message.

        Args:
            self (odoo.models.BaseModel): The current record of the model.

        Returns:
            None
        """
        if not 0 <= self.report_no_of_days <= 9999:
            raise ValidationError(_("Allow Value between 0 to 9999"))

    @api.constrains("pan")
    @api.onchange("pan")
    def _check_pan_validation(self):
        """
        This method validates the PAN number entered by the user.

        Raises:
            ValidationError:
                - If the PAN number is not 10 characters long.
                - If the PAN number contains characters other than alphanumeric (a-z, A-Z, 0-9).
        """
        if self.pan:
            if len(self.pan) != 10:
                raise ValidationError(_("Pan Number should be 10 characters long"))
            if not self.pan.isalnum():
                raise ValidationError(_("Please Enter Alphanumeric Value"))

    @api.constrains("cin")
    @api.onchange("cin")
    def _check_cin_validation(self):
        """
        This method validates the CIN number entered by the user.

        Raises:
            ValidationError:
                - If the CIN number is not 21 characters long.
                - If the CIN number contains characters other than alphanumeric (a-z, A-Z, 0-9).
        """
        if self.cin:
            if len(self.cin) != 21:
                raise ValidationError(_("CIN Number should be 21 characters long"))
            if not self.cin.isalnum():
                raise ValidationError(_("Please Enter Alphanumeric Value"))

    @api.constrains("name")
    @api.onchange("name")
    def _check_name_validation(self):
        """
        This method validates the name entered by the user.

        Raises:
            ValidationError:
                - If the name is < 3 and 128 > characters long.
        """
        if self.name:
            if len(self.name) < 3 or len(self.name) > 128:
                raise ValidationError(
                    _("Minimum 3 characters and maximum 128 characters allow")
                )

    @api.constrains("zip")
    @api.onchange("zip")
    def _check_zip_validation(self):
        """
        This method validates the zip entered by the user.
        Raises:
            ValidationError:
                - If the zip code is more than 14 digits long.
                - If the zip contains non-numeric characters.
        """
        for rec in self:
            if rec.zip:
                if not rec.zip.isdigit():
                    raise ValidationError("The Pincode must contain only numeric values.")

    @api.constrains("city")
    @api.onchange("city")
    def _check_city_validation(self):
        """
        This method validates the city entered by the user.
        Raises:
            ValidationError:
                - If the city is > 72 characters long.
        """
        if self.city and len(self.city) > 72:
            raise ValidationError(_("Maximum 72 characters allow"))

    @api.constrains("street")
    @api.onchange("street")
    def _check_street_validation(self):
        """
        This method validates the street entered by the user.
        Raises:
            ValidationError:
                - If the street is > 128 characters long.
        """
        if self.street and len(self.street) > 128:
            raise ValidationError(_("Maximum 128 characters allow"))

    @api.constrains("street2")
    @api.onchange("street2")
    def _check_street2_validation(self):
        """
        This method validates the street2 entered by the user.
        Raises:
            ValidationError:
                - If the street2 > 128 characters long.
        """
        if self.street2 and len(self.street2) > 128:
            raise ValidationError(_("Maximum 128 characters allow"))

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

    @api.onchange("logo")
    @api.constrains("logo")
    def _check_company_logo_validation(self):
        """
        This method validates the uploaded company logo:

        **Raises:**
            ValidationError: If the uploaded logo size exceeds 1MB.
        """
        if self.logo and len(self.logo) > 1048576:  # 1MB in bytes
            raise ValidationError("Image size cannot exceed 1MB.")

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

    @api.onchange("escalation_email")
    @api.constrains("escalation_email")
    def _check_email_ids(self):
        if self.escalation_email:
            # Split the emails by commas
            emails = [
                email.strip()
                for email in self.escalation_email.split(",")
                if email.strip()
            ]
            email_regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
            for email in emails:
                if not bool(re.fullmatch(email_regex, email)):
                    raise ValidationError(f"Invalid email ID: {email}")

    @api.model
    def get_model_description(self, model):
        get_model_name = self.env["ir.model"].search([("model", "=", model)]).name
        return {"model_name": get_model_name}

    @api.onchange("state_id")
    def onchange_state_id(self):
        if not self._context.get("is_res_company_location_view"):
            return

        main_company = self.env["res.company"].search(
            [("parent_id", "=", False), ("active", "=", True)], limit=1
        )

        if not self.state_id or not main_company:
            self.gst_no = False
            return

        # Check if the state exists in main company's GST invoice lines
        if self.state_id.name not in main_company.gst_invoice_line_ids.mapped("state"):
            self.gst_no = False
            return

        # Fetch GST details directly
        get_gst_rec = self.env["gst.details"].search(
            [
                ("company_id", "=", main_company.id),
                ("state", "ilike", self.state_id.name),
            ],
            limit=1,
        )
        self.gst_no = get_gst_rec.gst_no if get_gst_rec else False

    @api.constrains('gst_no')
    def _check_gst_no_active(self):
        main_company = self.search([('parent_id', '=', False), ('active', '=', True)], limit=1)

        if main_company:
            # Fetch all gst_integration_line_ids, including inactive ones
            all_gst_lines = self.env['gst.details'].with_context(active_test=False).search(
                [('company_id', '=', main_company.id)],
            )

            inactive_gst_nos = {line.gst_no for line in all_gst_lines if not line.active}

            for record in self:
                if record.gst_no in inactive_gst_nos:
                    raise ValidationError(_("GST number is inactive."))

    @api.constrains('phone')
    @api.onchange('phone')
    def _phone_numeric_validation(self):
        """
       This method validates the phone number entered by the user.
       Raises:
           ValidationError:
               - If the phone contains non-numeric characters.
       """
        for rec in self:
            if rec.phone:
                if not rec.phone.isdigit():
                    raise ValidationError("The phone number must contain only numeric values.")

    @api.model
    def write(self, vals):
        res = super().write(vals)
        if self._context.get('is_res_company_location_view'):
            self.check_shipping_line_capacity()
        return res

    def check_shipping_line_capacity(self):
        if self and self.shipping_line_mapping_ids:
            shipping_lines_capacity = self.shipping_line_mapping_ids.filtered(lambda r: r.active == True).mapped('capacity')
            capacities = [int(x) for x in shipping_lines_capacity if x is not False]
            total_sum = sum(capacities)
            if total_sum >= 0 and int(self.capacity) < total_sum:
                raise ValidationError(_('Capacity Added exceeds the location capacity'))

    @api.constrains('date_format')
    def change_date_format(self):
        """
        Change the date format as per the company format.
        """
        if not self.env.user.lang:
            return
        date_format_map = {
            'DD/MM/YYYY': "%d/%m/%Y",
            'YYYY/MM/DD': "%Y/%m/%d",
            'MM/DD/YYYY': "%m/%d/%Y"
        }
        new_date_format = date_format_map.get(self.date_format, "%m/%d/%Y")
        user_lang = self.env.user.lang
        lang = self.env['res.lang'].sudo()._activate_lang(user_lang)
        if lang:
            lang.sudo().write({'date_format': new_date_format})
