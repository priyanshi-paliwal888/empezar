# -*- coding: utf-8 -*-
import json
from odoo import fields, models, _, api
from odoo.exceptions import UserError, ValidationError
import requests
from .res_users import ResUsers


class GstDetails(models.Model):

    _name = "gst.details"
    _description = "Gst Details"
    _rec_name = "gst_no"

    gst_no = fields.Char(string="GST No.")
    tax_payer_type = fields.Char("TAXPAYER TYPE")
    state = fields.Char(string="STATE")
    state_jurisdiction = fields.Char(string="STATE JURISDICTION")
    status = fields.Char(string="STATUS")
    company_id = fields.Many2one(
        "res.company", string="Company Name", ondelete="cascade"
    )
    nature_of_business = fields.Char("NATURE OF BUSINESS")
    place_of_business = fields.Char("PRINCIPAL PLACE OF BUSINESS")
    additional_place_of_business = fields.Char("ADDITIONAL PLACE OF BUSINESS 1")
    nature_additional_place_of_business = fields.Char(
        "NATURE OF ADDITIONAL PLACE OF BUSINESS 1"
    )
    additional_place_of_business_2 = fields.Char("ADDITIONAL PLACE OF BUSINESS 2")
    nature_additional_place_of_business_2 = fields.Char(
        "NATURE OF ADDITIONAL PLACE OF BUSINESS 2"
    )
    last_update = fields.Char("LAST UPDATE ON")
    username = fields.Char("Username (E-Invoicing)")
    password = fields.Char("Password (E-Invoicing)")
    e_invoicing_status = fields.Boolean(string="E-invoicing Status", default=False)
    arn_no = fields.Char("ARN NO. (LUT)")
    date = fields.Date("Date")
    display_create_info = fields.Char(compute="_get_create_record_info")
    display_modified_info = fields.Char(compute="_get_modify_record_info")
    active = fields.Boolean("Status", default=True)
    is_e_invoice_applicable = fields.Boolean(compute="_get_e_inv_applicable_values")
    # fields for parties integration
    partner_id = fields.Many2one(
        "res.partner", string="Parties Name", ondelete="cascade"
    )
    legal_name = fields.Char(string="Legal Name")
    gst_pincode = fields.Char(string="Pin Code")
    parties_add_line_1 = fields.Char(string="Parties Address line 1")
    parties_add_line_2 = fields.Char(string="Parties Address line 2")
    gst_api_response = fields.Text(string="GST API Response")

    def _get_e_inv_applicable_values(self):
        if not self._context.get('is_cms_parties_view'):
            company_obj = self.env['res.company'].search([('parent_id', '=', False), ('active', '=', True)], limit=1)
            for rec in self:
                if company_obj and company_obj.e_invoice_applicable == "no":
                    rec.is_e_invoice_applicable = False
                else:
                    rec.is_e_invoice_applicable = True
        else:
            self.is_e_invoice_applicable = False

    def view_response(self):
        return {
            'type': 'ir.actions.act_window',
            'name': f'GST JSON - {self.gst_no}',
            'res_model': 'gst.details',
            'view_mode': 'form',
            'views': [(self.env.ref('empezar_base.gst_details_response_view').id, 'form')],
            'res_id': self.id,
            'target': 'new',
        }

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self._context.get("is_cms_parties_view"):
            res["partner_id"] = self._context.get("active_id") or False
            return res
        res["company_id"] = self._context.get("active_id")
        company_obj = self.env["res.company"].browse(self._context.get("active_id"))
        if company_obj and company_obj.e_invoice_applicable == "yes":
            res["is_e_invoice_applicable"] = True
        return res

    def get_gst_credentials(self):
        """
        This function return a gst credentials details.
        :return:
        """
        credentials = self.env["gst.credentials"].search([], limit=1)
        if credentials:
            email = credentials.email
            client_id = credentials.client_id
            client_secret = credentials.client_secret
            return email, client_id, client_secret
        return {"error": "GST Credentials Not Found."}
        # raise ValidationError(_("GST Credentials Not Found."))

    @api.model
    def get_gst_data(self, **kwargs):
        """
        fetch data from gst api.
        :return:
        """
        gst_url = "https://api.mastergst.com/public/search"
        try:
            gst_no = kwargs.get("gst_no")
            company_id = kwargs.get("company_id")
            record_id = kwargs.get("record_id")
            partner_id = kwargs.get("partner_id")
            if not gst_no:
                return {"error": "Please Add Gst Number."}
            if not partner_id:
                if not company_id:
                    return {"error": "Company Is not defined."}
                if not record_id:
                    data = self._check_gst_data_validation(gst_no, company_id)
                    if data and data.get("error"):
                        return data
            else:
                if not partner_id:
                    return {"error": "Parties not defined."}
                if not record_id:
                    data = self.check_parties_gst_validation(gst_no, partner_id)
                    if data and data.get("error"):
                        return data
        except Exception as e:
            err = f"Other error occurred: {e}"
            return {"error": err}

        email, client_id, client_secret = self.get_gst_credentials()
        # query parameters
        query_params = {"email": email, "gstin": gst_no}

        # Define your headers
        headers = {
            "client_id": client_id,
            "client_secret": client_secret,
        }

        # Make the request and handle the errors.
        try:
            response = requests.get(gst_url, headers=headers, params=query_params)
            response.raise_for_status()  # Raise an exception for HTTP errors
            # Process the response data
            data = response.json()
            if data.get("error") or data.get("status_cd") == "0":
                status_desc = data.get("status_desc", "")
                error_cd = data.get("error", {}).get("error_cd", "")
                error_message = data.get("error", {}).get("message", "")
                error = f"{status_desc} {error_cd} : {error_message}"
                if error_message and error_message == 'Invalid GSTIN / UID':
                    error = 'GST Number is not found in GST Portal. Please enter the correct GST Number.'
                elif error_message and error_message == 'java.net.UnknownHostException: devapi.gst.gov.in':
                    error = 'Please try again after some time.'
                return {"error": error}
            response_data = data
        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 404:
                return {
                    "error": "GST Number is not found in GST Portal. Please enter correct GST Number"
                }
            elif response.status_code == 500:
                return {
                    "error": "Error receiving GST details from GST Portal. Retry after some time."
                }
            raise UserError(f"HTTP error occurred: {http_err}")
        except Exception as err:
            err = f"Other error occurred: {err}"
            return {"error": err}
        return response_data

    @api.model
    def get_gst_data_for_parties(self, **kwargs):
        """
        fetch data from gst api.
        :return:
        """
        gst_url = "https://api.mastergst.com/public/search"
        try:
            gst_no = kwargs.get("gst_no")
            record_id = kwargs.get("record_id")
            partner_id = kwargs.get("partner_id")
            if not gst_no:
                return {"error": "Please Add Gst Number."}
            if not record_id:
                data = self.check_parties_gst_validation(gst_no, partner_id)
                if data and data.get("error"):
                    return data
        except Exception as e:
            err = f"Other error occurred: {e}"
            return {"error": err}

        email, client_id, client_secret = self.get_gst_credentials()
        # query parameters
        query_params = {"email": email, "gstin": gst_no}

        # Define your headers
        headers = {
            "client_id": client_id,
            "client_secret": client_secret,
        }

        # Make the request and handle the errors.
        try:
            response = requests.get(gst_url, headers=headers, params=query_params)
            response.raise_for_status()  # Raise an exception for HTTP errors
            # Process the response data
            data = response.json()
            if data.get("error") or data.get("status_cd") == "0":
                status_desc = data.get("status_desc", "")
                error_cd = data.get("error", {}).get("error_cd", "")
                error_message = data.get("error", {}).get("message", "")
                error = f"{status_desc} {error_cd} : {error_message}"
                if error_message and error_message == 'Invalid GSTIN / UID':
                    error = 'GST Number is not found in GST Portal. Please enter the correct GST Number.'
                elif error_message and error_message == 'java.net.UnknownHostException: devapi.gst.gov.in':
                    error = 'Please try again after some time.'
                return {"error": error}
            response_data = data
        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 404:
                return {
                    "error": "GST Number is not found in GST Portal. Please enter correct GST Number"
                }
            elif response.status_code == 500:
                return {
                    "error": "Error receiving GST details from GST Portal. Retry after some time."
                }
            raise UserError(f"HTTP error occurred: {http_err}")
        except Exception as err:
            err = f"Other error occurred: {err}"
            return {"error": err}
        return response_data

    def _validate_gst_number(self, gst_no, company_id):
        if len(gst_no) != 15:
            return {
                "error": "GST Number entered should be 15 characters long. Please enter correct GST Number."
            }
        if not gst_no.isalnum():
            return {"error": "Please Enter Alphanumeric Value"}

        company_obj = self.env["res.company"].browse(company_id)
        existing_gst_nos = self.search(
            [("company_id", "=", company_id), ("id", "!=", self.id)]
        ).mapped("gst_no")

        if gst_no in existing_gst_nos:
            return {
                "error": f"{gst_no} is already added. Please enter another GST No."
            }

        company_pan_no = company_obj.pan
        if company_pan_no and gst_no[2:12] != company_pan_no:
            return {
                "error": "GST No. does not match the PAN. Please enter a Valid GST No."
            }

        return {"success": "true"}

    def _validate_parties_gst_number(self, gst_no, partner_id=None):
        if len(gst_no) != 15:
            return {
                "error": "GST Number entered should be 15 characters long. Please enter correct GST Number."
            }
        if not gst_no.isalnum():
            return {"error": "Please Enter Alphanumeric Value"}

        if partner_id:
            partner_obj = self.env["res.partner"].browse(partner_id)
            existing_gst_nos = self.search(
                [("partner_id", "!=", False), ("id", "!=", self.id)]
            ).mapped("gst_no")

            if gst_no in existing_gst_nos:
                partner_id = self.env['res.partner'].search([('gst_no', '=', gst_no)], limit=1)
                return {"error": "%s GST Number already set for %s. Please enter a different GST No." % (
                gst_no, partner_id.name)}

            parties_pan_no = partner_obj.l10n_in_pan
            if parties_pan_no and gst_no[2:12] != parties_pan_no:
                return {"error": "GST Number entered does not match with the existing PAN"}

        return {"success": "true"}

    def check_gst_validations(self):
        """
        Check GST validations.
        """
        if not self._context.get("is_cms_parties_view"):
            if self.gst_no and self.company_id:
                validation_result = self._validate_gst_number(
                    self.gst_no, self.company_id.id
                )
                if "error" in validation_result:
                    raise ValidationError(_(validation_result["error"]))
        elif self._context.get("is_cms_parties_view"):
            if self.gst_no and self.partner_id:
                validation_result = self._validate_parties_gst_number(
                    self.gst_no, self.partner_id.id
                )
                if "error" in validation_result:
                    raise ValidationError(_(validation_result["error"]))
                partner_obj = self.env["res.partner"].browse(self.partner_id.id)
                if not partner_obj.l10n_in_pan:
                    partner_obj.l10n_in_pan = self.gst_no[2:12]
                if self.state:
                    partner_obj.gst_state = self.state
                if self.legal_name:
                    partner_obj.party_name = self.legal_name
                if self.gst_pincode:
                    partner_obj.zip = self.gst_pincode
                if self.parties_add_line_1:
                    partner_obj.street = self.parties_add_line_1
                if self.parties_add_line_2:
                    partner_obj.street2 = self.parties_add_line_2

    def _check_gst_data_validation(self, gst_no, company_id):
        """
        Check GST data validations.
        """
        if gst_no and company_id:
            return self._validate_gst_number(gst_no, company_id)
        return {"error": "Some issue while validating the GST Number"}

    def check_parties_gst_validation(self, gst_no, partner_id=None):
        """
        Check GST data validations.
        """
        if gst_no:
            return self._validate_parties_gst_number(gst_no, partner_id)
        return {"error": "Some issue while validating the GST Number"}

    @api.constrains("gst_no")
    def is_valid_gst_no(self):
        """
        validate the gst number and update the data as per the api response.
        :return:
        """
        self.check_gst_validations()

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

    @api.constrains('active')
    def _active_gst_no(self):
        for record in self:
            if record.partner_id.is_gst_applicable == "yes" and record.partner_id.parties_gst_invoice_line_ids:
                # Get all active GST invoice line records
                active_lines = record.partner_id.parties_gst_invoice_line_ids.filtered(
                    lambda line: line.status == 'Active')

                if not record.active:
                    if len(active_lines) == 1 and record in active_lines:
                        raise ValidationError(
                            "Cannot disable the record while the only active GST invoice line exists.")
