# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from .res_users import ResUsers
from .contrainer_type_edi import ContainerTypeEdi


class ProductTemplate(models.Model):
    _inherit = "product.template"

    charge_name = fields.Char(string="Charge Name", size=128)
    charge_code = fields.Char(string="Charge Code", size=16)
    gst_rate = fields.Many2many(
        comodel_name="account.tax",
        relation="product_taxes_rel",
        column1="prod_id",
        column2="tax_id",
        help="Default taxes used when selling the product.",
        string="GST Rate",
        domain=[("type_tax_use", "=", "sale"), ("active", "=", True)],
    )
    is_chargeable_product = fields.Boolean("Is Chargeable Product", default=False)
    invoice_type = fields.Selection(
        [
            ("lift_off", "Lift Off"),
            ("lift_on", "Lift On"),
            ("Others", "Others"),
        ],
        string="Invoice Type",
    )
    gst_applicable = fields.Selection(
        [
            ("yes", "Yes"),
            ("no", "No"),
        ],
        default="yes",
    )
    display_create_info = fields.Char(compute="_get_create_record_info")
    display_modified_info = fields.Char(compute="_get_modify_record_info")
    rec_status = fields.Selection(
        [
            ("active", "Active"),
            ("disable", "Disable"),
        ],
        default="active",
        compute="_check_active_records",
        string="Status",
    )
    hsn_code = fields.Many2one("master.hsn.code", string="HSN/SAC Code")
    descriptions = fields.Char(string="Charge Description", size=255)

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

    @api.model_create_multi
    def create(self, vals_list):
        """
        Assign custom field values while create a record from custom product view.
        :param vals_list:
        :return:
        """
        if self._context.get("is_charge_product_view"):
            product_tag_id = self.env.ref("empezar_base.empezar_charge_product_tag").id
            for vals in vals_list:
                vals.update(
                    {
                        "name": vals.get("charge_name"),
                        "default_code": vals.get("charge_code"),
                        "is_chargeable_product": True,
                        "product_tag_ids": [product_tag_id],
                        "detailed_type": "service",
                    }
                )
                if vals.get('gst_rate'):
                    vals.update({"taxes_id": [(6, 0, id) for id in vals.get("gst_rate")]})
        for vals in vals_list:
            if vals.get("is_chargeable_product") and vals.get("gst_applicable") == "no":
                vals.update({"hsn_code": "", "taxes_id": [(5, 0, 0)]})
        res = super().create(vals_list)
        return res

    def write(self, vals):
        if vals.get("gst_applicable") == "no":
            vals["hsn_code"] = ""
            vals["taxes_id"] = [(5, 0, 0)]
        return super().write(vals)

    @api.constrains("charge_name", "charge_code", "invoice_type")
    def _constrains_name(self):
        existing_products = self.env["product.template"].search(
            [("active", "=", True), ("id", "!=", self.id)]
        )
        names = existing_products.mapped("charge_name")
        codes = existing_products.mapped("charge_code")
        invoice_types = existing_products.mapped("invoice_type")
        if self.charge_name and self.charge_name in names:
            raise ValidationError(
                _(
                    "Charge with the same name is already present. Please enter a valid Charge Name."
                )
            )
        if self.charge_code and self.charge_code in codes:
            raise ValidationError(
                _(
                    "Charge with the same code is already present. Please enter a valid Charge Code."
                )
            )
        if (
            self.invoice_type
            and self.invoice_type in ["lift_off", "lift_on"]
            and self.invoice_type in invoice_types
        ):
            raise ValidationError(
                _(
                    "Charge for the selected invoice type is already present. Please select different invoice type."
                )
            )

    @api.constrains("active")
    def charge_is_active(self):
        """ Check weather a charge is active or not based on invoice type"""
        for record in self:
            # Only apply the constraint for the specified invoice types
            if record.invoice_type in ["lift_off", "lift_on"] and record.active and record.rec_status == "active":
                existing_charges = self.env["product.template"].search([
                    ("active", "=", True),
                    ("id", "!=", record.id)
                ])
                if existing_charges.filtered(
                        lambda charge: charge.invoice_type == record.invoice_type and charge.rec_status == "active"):
                    raise ValidationError(
                        _("Charge for the selected invoice type is already present. Please select a different invoice type.")
                    )

    @api.onchange("gst_applicable")
    def _clear_taxes_id(self):
        if self.gst_applicable == "no":
            self.gst_rate = False
            self.hsn_code = False
