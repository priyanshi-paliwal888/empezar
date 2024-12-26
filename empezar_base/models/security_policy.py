# -*- coding: utf-8 -*-

import ipaddress
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class SecurityPolicy(models.Model):

    _name = "security.policy"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Security Policy"

    name = fields.Char(string="Policy Name", tracking=True)
    ip_address = fields.Char("Ip Address", tracking=True)
    access = fields.Selection(
        [
            ("allow", "Allow"),
            ("deny", "Deny"),
        ],
        tracking=True,
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("name_uniq", "unique (name)", "Policy name already exists!"),
        (
            "name_check",
            "CHECK(LENGTH(name) <= 32)",
            "Policy name cannot exceed 32 characters",
        ),
    ]

    @api.constrains("ip_address")
    @api.onchange("ip_address")
    def _check_ip_address(self):
        """
        This method is triggered whenever the `ip_address` field is changed in the Odoo form.

        It validates the entered IP address to ensure it's a valid format using the `ipaddress` library.

        Raises:
            ValidationError: If the entered IP address is invalid. The error message will be displayed to the user
                            in the Odoo form.
        """
        try:
            ip_addr = ipaddress.ip_network(self.ip_address)
        except ValueError:
            raise ValidationError(
                _("Ip Address entered is invalid. kindly enter valid IP Address")
            )
