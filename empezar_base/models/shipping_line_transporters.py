# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from .res_users import ResUsers


class ShippingLineTransporters(models.Model):

    _name = "shipping.line.transporters"
    _description = "Shipping Line Transporters"

    def _get_domain(self):
        get_transporter_id = self.env.ref("empezar_base.cms_parties_type_5").id
        domain = (
            self.env["res.partner"]
            .search([])
            .filtered(lambda record: get_transporter_id in record.parties_type_ids.ids)
        )
        return [("id", "in", domain.ids)]

    transporter_id = fields.Many2one(
        "res.partner", string="Transporter Name", required=True, domain=_get_domain
    )
    code = fields.Char(
        string="Transporter Code", required=True, size=10, translate=True
    )
    partner_id = fields.Many2one("res.partner", ondelete="cascade")
    display_create_info = fields.Char(compute="_get_create_record_info")
    display_modified_info = fields.Char(compute="_get_modify_record_info")
    active = fields.Boolean("Status", default=True)
    company_id = fields.Many2one("res.company")
    rec_status = fields.Selection(
        [
            ("active", "Active"),
            ("disable", "Disable"),
        ],
        default="active",
        compute="_check_active_records",
        string="Status",
    )

    @api.constrains("code", "transporter_id")
    def _constrains_code(self):
        for rec in self:
            existing_codes = rec.env["shipping.line.transporters"].search(
                [("id", "!=", rec.id)]
            )
            codes = existing_codes.mapped("code")
            if rec.code in codes:
                existing_code_record = existing_codes.filtered(
                    lambda r, code=rec.code: r.code == code
                )
                transporter_name = (
                    existing_code_record.transporter_id.name
                    if existing_code_record
                    else None
                )
                raise ValidationError(
                    _(
                        "Transporter '%s' with the same code already exists."
                        % transporter_name
                    )
                )

    @api.constrains("transporter_id")
    def _constrains_name(self):
        for rec in self:
            existing_transporters = rec.env["shipping.line.transporters"].search(
                [("partner_id", "=", rec.partner_id.id), ("id", "!=", rec.id)]
            )
            names = existing_transporters.mapped("transporter_id")
            if rec.transporter_id in names:
                raise ValidationError(
                    _("Name already exists for the selected transporter.")
                )

    def _check_active_records(self):
        """
        This method iterates through all records in the current recordset
        and updates their `rec_status` field based on the value of the
        `active` field.

        - If a record's `active` field is True, the `rec_status` field is set to "active".
        - If a record's `active` field is False, the `rec_status` field is set to "disabled".

        Args:
            self (Recordset): The current recordset of the model.
        """
        for rec in self:
            if rec.active:
                rec.rec_status = "active"
            else:
                rec.rec_status = "disable"

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

    @api.onchange('transporter_id')
    def _onchange_container_type_data_id(self):
        """
        Test that a transporter_id is not active raises a ValidationError.
        """
        if self.transporter_id and not self.transporter_id.active:
            raise ValidationError('Please Select an active Transporter.')
