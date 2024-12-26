from odoo import models

class EditEstimateWizard(models.TransientModel):
    _name = 'edit.estimate.wizard'
    _description = 'Edit Estimate Wizard'

    def action_confirm_edit_estimate(self):
        """Method to confirm the edit estimate wizard."""

        repair_pending_id = self.env.context.get('active_id')
        repair_pending_record = self.env['repair.pending'].browse(repair_pending_id)
        if repair_pending_record.repair_status == 'approved':
            existing_estimate = self.env['repair.pending.estimates'].search([
            ('pending_id', '=', repair_pending_id)
        ], limit=1)
            if existing_estimate:
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Estimate Form',
                    'res_model': 'repair.pending.estimates',
                    'view_mode': 'form',
                    'views': [(self.env.ref('empezar_repair.view_estimates_form').id, 'form')],
                    'res_id': existing_estimate.id,
                    'target': 'current',
                }


    def action_cancel(self):
        """Method to cancel the edit estimate wizard."""

        return {'type': 'ir.actions.act_window_close'}

