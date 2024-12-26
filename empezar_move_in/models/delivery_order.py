from odoo import models, api


class DeliveryOrder(models.Model):
    _inherit = "delivery.order"

    @api.model
    def default_get(self, fields_list):
        """Set default values for fields based on context flags."""
        res = super().default_get(fields_list)
        context = self.env.context
        if context.get('is_from_move_out'):
            if context.get('is_from_delivery_order'):
                delivery_no = context.get('default_name')
                location_id = context.get('location_id')
                res.update({
                    'delivery_no': delivery_no,
                    'location': [(6, 0, [location_id])]
                })
        return res
