from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MonthlyLockWizard(models.TransientModel):
    _name = "monthly.lock.wizard"
    _description = "Monthly Lock Wizard"

    action = fields.Selection([('lock', 'Lock'), ('unlock', 'Unlock')], string="Action",
                              required=True)
    remarks = fields.Char(string="Remarks", size=64)
    username = fields.Char(string="Username", required=True,
                           default=lambda self: self.env.user.name)
    invoice_type = fields.Selection(
        [
            ("invoice", "Invoice"),
            ("credit", "Credit"),
        ], string="Type")

    def action_confirm_lock(self):
        """Lock the selected records and store the action in MonthlyLockHistory model."""
        # Retrieve active_id or active_ids from the context
        active_ids = self._context.get('active_ids') or [self._context.get('active_id')]
        if not active_ids:
            raise ValidationError(_("No records selected to lock."))

        for monthly_lock in self.env['monthly.lock'].browse(active_ids):
            # Check if the record is already locked
            if monthly_lock.is_locked:
                raise ValidationError(
                    _("One of the selected records is already locked. You cannot lock it again."))

            # Create the history record for each record
            self.env['monthly.lock.history'].create({
                'monthly_lock_id': monthly_lock.id,
                'action': 'lock',
                'remarks': self.remarks,
                'username': self.username,
                'date_time': fields.Datetime.now(),
                'invoice_type': self.invoice_type
            })

            # Lock the record
            monthly_lock.is_locked = True

        return {'type': 'ir.actions.act_window_close'}

    def action_confirm_unlock(self):
        """Unlock the selected records and store the action in MonthlyLockHistory model."""
        # Retrieve active_id or active_ids from the context
        active_ids = self._context.get('active_ids') or [self._context.get('active_id')]
        if not active_ids:
            raise ValidationError(_("No records selected to unlock."))

        for monthly_lock in self.env['monthly.lock'].browse(active_ids):
            # Check if the record is already unlocked
            if not monthly_lock.is_locked:
                raise ValidationError(
                    _("One of the selected records is already unlocked. You cannot unlock it again."))

            # Create the history record for each record
            self.env['monthly.lock.history'].create({
                'monthly_lock_id': monthly_lock.id,
                'action': 'unlock',
                'remarks': self.remarks,
                'username': self.username,
                'date_time': fields.Datetime.now(),
                'invoice_type': self.invoice_type
            })

            # Unlock the record
            monthly_lock.is_locked = False

        return {'type': 'ir.actions.act_window_close'}
