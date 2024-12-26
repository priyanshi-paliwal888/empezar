# -*- coding: utf-8 -*-

import re
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class EInvoiceCredentials(models.Model):

    _name = "e.invoice.credentials"
    _description = "E-Invoice Credentials"
    _rec_name="username"

    email = fields.Char(string="Email", required=True)
    username = fields.Char(string="Username", required=True)
    password = fields.Char(string="Password", required=True)
    ip_address = fields.Char(string="IP Address", required=True)
    client_id = fields.Char(string="Client ID", required=True)
    client_secret = fields.Char(string="Client Secret", required=True)
    gstin = fields.Char(string="GSTIN", required=True)
    is_auth_done = fields.Boolean(copy=False)

    @api.constrains("email")
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
