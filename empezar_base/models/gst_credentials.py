# -*- coding: utf-8 -*-

import re
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class GstCredentials(models.Model):

    _name = "gst.credentials"
    _description = "Gst Credentials"
    _rec_name = "email"

    email = fields.Char(string="Email", required=True)
    client_id = fields.Char(string="Client Id", required=True)
    client_secret = fields.Char(string="Client Secret", required=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        readonly=True,
        default=lambda self: self.env.company,
    )

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
