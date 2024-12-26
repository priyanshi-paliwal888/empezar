from odoo import models
from datetime import datetime
class ShippingLineConfirmationWizard(models.TransientModel):
    _name = 'shipping.line.confirmation.wizard'
    _description = 'Shipping Line Confirmation Wizard'

    def action_confirm_send_to_shipping_line(self):
        """Method to confirm the send to shipping line confirmation wizard."""

        estimate_record = self.env['repair.pending.estimates'].browse(self._context.get('active_id'))

        current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        estimate_record.write({'estimate_date_and_time': current_datetime})

        estimate_record.pending_id.write({'repair_status': 'awaiting_approval'})
        # estimate_record.action_send_to_shipping_line()
        estimate_record.send_westim_edi()

    def cancel(self):
        """Method to cancel the send to shipping line confirmation wizard."""

        return {'type': 'ir.actions.act_window_close'}

