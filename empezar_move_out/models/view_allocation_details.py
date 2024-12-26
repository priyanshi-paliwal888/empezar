from odoo import fields, models, api,_


class ContainerDetailsWizard(models.Model):
    _inherit = 'view.update.allocation'

    related_moves_ids = fields.Many2many('move.out', string='Related Moves')
    related_moves_in = fields.Many2many('move.in', string="Related Move In")

    def button_save(self):
        pass
    def button_cancel(self):
        pass

    def view_records(self):
        for record in self:
            if record.delivery_order_id:
                # Ensure that container_size_type_values is initialized properly
                context = {
                    'default_delivery_order_id': record.delivery_order_id.id,
                }

                # Add related moves to context if they exist
                if record.related_moves_ids:
                    context['default_related_moves_ids'] = record.related_moves_ids.ids
                if record.related_moves_in:
                    context['default_related_moves_in'] = record.related_moves_in.ids

                # Open the form view with the related moves data in context
                return {
                    'name': _('View Allocations'),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',  # Open in form view
                    'res_model': 'view.update.allocation',
                    'target': 'new',
                    'view_id': self.env.ref('empezar_move_out.view_update_allocation_form').id,
                    'context': context,
                }








