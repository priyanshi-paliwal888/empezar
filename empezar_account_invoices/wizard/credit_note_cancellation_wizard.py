import requests
from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json

class CreditCancellationWizard(models.TransientModel):
    _name = 'credit.note.cancellation.wizard'
    _description = 'Credit Note Cancellation Wizard'

    credit_id = fields.Many2one("credit.note.invoice", "Credit ID")
    cancellation_reason = fields.Many2one("cancellation.reason", string='Cancellation Reason', required=True, store=True)
    cancellation_remarks = fields.Char('Cancellation Remarks',size=64)
    auth_token = fields.Char(store=True)
    irn_number = fields.Char(store=True)

    def confirm_credit_cancellation(self):
        if not self.credit_id:
            return
        error_messages = []
        fiscal_year_id = self.env['account.fiscal.year'].search([('date_from', '<=', self.credit_id.credit_note_date), ('date_to', '>=', self.credit_id.credit_note_date)],limit=1)
        credit_month = self.credit_id.credit_note_date.month
        location = self.env['monthly.lock'].search([
            ('fiscal_year','=',fiscal_year_id.id),
            ('location_id', '=', self.credit_id.location_id.name),
            ('month', '=', credit_month),
            ('invoice_type', '=', "credit")
        ], limit=1)

        if location and location.is_locked:
            raise ValidationError(_(
                "Credit Note cannot be cancelled as it is already locked. Please contact system admin for further support."))
        invoice_ref_number = self.env['move.in.out.invoice'].search(
            [('invoice_number', '=', self.credit_id.invoice_reference_no)])

        if invoice_ref_number.e_invoice == 'yes':
            # Ensure 'e_invoice_create_date' is available in the invoice model
            e_invoice_create_date = fields.Datetime.to_datetime(self.credit_id.ack_date)
            current_date_time = fields.Datetime.now()

            if e_invoice_create_date:
                # Calculate time difference in IST
                time_difference = current_date_time - e_invoice_create_date
                if time_difference > timedelta(hours=24):
                    raise ValidationError(
                        "Credit Note cannot be cancelled as 24 hours have already passed since GST posting"
                    )
                if self.irn_number:
                    try:
                        api_response = self.authenticate_einvoice_api()
                        if api_response and api_response['status_cd'] == 'Sucess':
                            auth_token = api_response['data'].get('AuthToken')
                            if auth_token:
                                self.auth_token = auth_token
                                cancel_response = self.cancel_irn()
                                if cancel_response and cancel_response.get('status_cd') != '1':
                                    raise ValidationError(f"ERROR{cancel_response}")
                                else:
                                    self.credit_id.irn_status = "cancelled"
                                    self.credit_id.write({'credit_note_status': 'cancelled'})
                        else:
                            error_messages = json.loads(api_response['status_desc'])

                            # Prepare a structured output
                            errors = []
                            for error in error_messages:
                                errors.append(
                                    f"ErrorMessage: {error['ErrorMessage']}")

                            # Join all error messages into a single string or store them in a field
                            all_errors = "\n".join(errors)
                            self.credit_id.response_error = all_errors
                            raise ValidationError(f"ERROR{self.invoice_id.response_error}")
                    # except Exception as e:
                    #     # Handle any exception during IRN generation
                    #     print(f"Error generating IRN: {e}")

                    except requests.exceptions.RequestException as req_err:
                        print("Request exception occurred:", req_err)
                        return None
                else:
                    raise ValidationError(
                        f"Cannot cancel E-Invoice .{self.credit_id.response_error}")
            else:
                # Proceed to cancel the invoice
                self.credit_id.write({'credit_note_status': 'cancelled'})
        else:
            self.credit_id.write({'credit_note_status': 'cancelled'})

    @api.model
    def authenticate_einvoice_api(self):
        url = "https://api.mastergst.com/einvoice/authenticate"
        username, password, ip_address, email, client_id, client_secret, gstin = self.get_e_invoice_authentication_token()
        if all([username, password, ip_address, email, client_id, client_secret, gstin]):
            headers = {
                "username": username,
                "password": password,
                "ip_address": ip_address,
                "client_id": client_id,
                "client_secret": client_secret,
                "gstin": gstin
            }

            params = {
                "email": email
            }

            try:
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                response_data = response.json()
                return response_data
            except requests.exceptions.RequestException as e:
                print("Error:", e)
                return None
        pass

    def get_e_invoice_authentication_token(self):
        """
        This function return e-invoice credentials details.
        :return:
        """
        credentials = self.env["e.invoice.credentials"].search([], limit=1)
        if credentials:
            username = credentials.username
            password = credentials.password
            ip_address = credentials.ip_address
            email = credentials.email
            client_id = credentials.client_id
            client_secret = credentials.client_secret
            gstin = credentials.gstin
            return username, password, ip_address, email, client_id, client_secret, gstin
        return {"error": "GST Credentials Not Found."}

    def cancel_irn(self):
        url = "https://api.mastergst.com/einvoice/type/CANCEL/version/V1_03"

        # Fetch required credentials and token
        username, password, ip_address, email, client_id, client_secret, gstin = self.get_e_invoice_authentication_token()

        # Set request headers
        headers = {
            "username": username,
            "password": password,
            "ip_address": ip_address,
            "client_id": client_id,
            "client_secret": client_secret,
            "gstin": gstin,
            "auth-token": self.auth_token,
            "Content-Type": "application/json"
        }

        # Additional parameters
        params = {
            "email": email
        }
        wizard = self.env['invoice.cancellation.wizard'].browse(self._context.get('active_id'))
        # Prepare the body data to send in the POST request
        body_data = {
            "IRN": self.irn_number,
            "CnlRsn": str(self.cancellation_reason.id),
            "CnlRem": self.cancellation_remarks
        }

        try:
            # Send POST request with JSON payload
            response = requests.post(url, headers=headers, params=params, json=body_data)
            try:
                if response.text:
                    response.raise_for_status()
                    response_data = response.json()
                    print("Response Data:", response_data)
                    return response_data
                else:
                    pass
            except requests.exceptions.RequestException as req_err:
                print("Request exception occurred:", req_err)
                return None

        except requests.exceptions.RequestException as req_err:
            print("Request exception occurred:", req_err)
            return None
