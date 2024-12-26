# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class MovementSetting(models.Model):

    _name = "movement.setting"
    _description = "Movement Setting"

    field_name = fields.Many2one(
        "ir.model.fields",
        string="Field Name",
        domain="[('model_id.name','=','Move In')]",
    )
    field_name_move_out = fields.Many2one(
        "ir.model.fields",
        string="Field Name",
        domain="[('model_id.name','=','Move Out')]",
    )
    show_on_screen = fields.Boolean(string="Show On Screen", default=False)
    mandatory = fields.Selection([("yes", "Yes"), ("no", "No")], string="Mandatory")
    company_id = fields.Many2one("res.company", string="Company", ondelete="cascade")
    movement_type = fields.Selection(
        [("move_in", "Move In"), ("move_out", "Move Out")],
        string="Movement Type",
        required=True,
    )

    @api.constrains('mandatory', 'show_on_screen')
    def _check_mandatory_show_on_screen(self):
        for record in self:
            if record.mandatory == "yes" and not record.show_on_screen:
                raise ValidationError("If 'Mandatory' is set to 'Yes', 'Show On Screen' must be True.")

    @api.onchange("show_on_screen")
    def onchange_show_on_screen(self):
        if self.show_on_screen:
            self.mandatory = "yes"
        else:
            self.mandatory = "no"

    @api.model
    def create(self, vals):
        if self.env.context.get("default_movement_type"):
            vals["movement_type"] = self.env.context.get("default_movement_type")
        return super().create(vals)

    @api.constrains("field_name")
    def check_location_validations(self):
        if not self.company_id.active:
            raise ValidationError(
                _("This action cannot be performed as the location is disabled.")
            )

    @api.constrains('field_name')
    def validation_field_name(self):
        if self.field_name:
            existing_record = self.env['movement.setting'].search(
                [('field_name.name', '=', self.field_name.name),
                 ('movement_type', '=', 'move_in'),
                 ('id', '!=', self.id),
                 ('company_id', '=', self.company_id.id)])

            if existing_record:
                raise ValidationError(
                    _("This field name has already been added before for Move In."))

    @api.constrains('field_name_move_out')
    def validation_field_name_move_out(self):
        if self.field_name_move_out:
            existing_record = self.env['movement.setting'].search(
                [('field_name_move_out.name', '=', self.field_name_move_out.name),
                 ('movement_type', '=', 'move_out'),
                 ('id', '!=', self.id),
                 ('company_id', '=', self.company_id.id)])

            if existing_record:
                raise ValidationError(
                    _("This field name has already been added before for Move Out."))
