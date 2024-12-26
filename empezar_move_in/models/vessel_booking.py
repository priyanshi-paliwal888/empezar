from odoo import models, api


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
