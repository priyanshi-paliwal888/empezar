from odoo import models, api,fields, _

class SealViewHistory(models.Model):
    _inherit = 'seal.management'
    _description = 'Seal View History'

    @api.constrains('rec_status')
    def _track_status_changes(self):
        for rec in self:
            if rec.rec_status:

                activity = ''
                if rec.rec_status == 'used':
                    activity = 'Move Out'
                elif rec.rec_status == 'damaged':
                    activity = 'Update Status'
                elif rec.rec_status == 'available':
                    # Check if there's a previous history record with activity 'add'
                    previous_history = self.env['seal.history'].search([('seal_id', '=', rec.id)],limit=1)
                    if previous_history and previous_history.activity == 'Add':
                        activity = 'Move In'
                    else:
                        activity = 'Add'

            # Create a new history record whenever the status changes
                self.env['seal.history'].create({
                    'seal_id': rec.id,
                    'rec_status': rec.rec_status,
                    'activity': activity,
                    'container_number':rec.container_number,
                    'user_name': rec.env.user.login,
                    'date_changed': fields.Datetime.now(),
                })


    def action_seal_view_history(self):

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'seal.history',
            'view_mode': 'tree',
            'view_id': self.env.ref('empezar_move_out.view_seal_history_tree').id,  # Ensure this is the correct view ID
            'domain': [('seal_id', '=', self.id)],  # Filter history by current seal
            'target': 'new',  # Open in a new window
        }