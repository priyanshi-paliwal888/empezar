# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class VesselBooking(models.Model):
    _inherit = "vessel.booking"

    @api.model
    def default_get(self, fields_list):
        """Set default values for fields based on context flags."""
        res = super().default_get(fields_list)
        context = self.env.context

        if context.get('is_from_move_out'):
            if context.get('is_from_vessel_booking'):
                booking_no = context.get('default_name')
                location_id = context.get('location_id')
                res.update({
                    'booking_no': booking_no,
                    'location': [(6, 0, [location_id])]
                })
        return res

    def unlink_container_record(self):
        """
        wizard action for unlink container number
         :return:
        """
        self.ensure_one()
        selected_records = self.container_numbers.filtered(lambda r: r.is_unlink)
        # for record in selected_records:
        #     new_record = (record.name).split(' ')[0]
        #     # move_in = self.env['move.in'].search([]).mapped('container')
        #     move_out = self.env['move.out'].search([]).mapped('container_id').mapped('name')
        #     # if new_record in move_in and new_record in move_out:
        #     if new_record in move_out:
        #         raise ValidationError(
        #             _(f"Container ({record.name}) cannot be unlinked as it is already moved out"))

        if selected_records:
            return {
                'name': _('Unlink Container Number'),
                'type': 'ir.actions.act_window',
                'res_model': 'unlink.container.wizard',
                'views': [[False, 'form']],
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_container_ids': [(6, 0, selected_records.ids)]
                }
            }

    @api.constrains('active')
    def _check_booking_active_constraint(self):
        """Ensures that if there is an existing Move Out record, the active field is set to False."""
        for record in self:
            if record.booking_no:
                if not record.active:
                    # Check if there's an active record with the same booking_no and not this record
                    move_out_records = self.env['move.out'].search([
                        ('active', '=', True),
                        ('booking_no_id', '=', record.booking_no),
                    ])
                    move_in_records = self.env['move.in'].search([
                        ('active', '=', True),
                        ('booking_no_id', '=', record.booking_no),
                    ])
                    if move_out_records:
                        raise ValidationError(_("Cannot archive a record Booking Number already exist in Move out."))
                    if move_in_records:
                        raise ValidationError(_("Cannot archive a record Booking Number already exist in Move in."))