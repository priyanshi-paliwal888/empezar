from odoo import fields, models, api, _


class ContainerDetails(models.Model):
    _inherit = "container.details.delivery"

    count = fields.Integer("Count", compute='_compute_count')
    related_moves = fields.Many2many('move.out', string='Related Moves')
    related_moves_in = fields.Many2many('move.in', string="Related Move In")

    def _compute_count(self):
        for record in self:
            record.count = 0
            if record.delivery_id:
                container_yard_ids = record.mapped('container_yard').ids
                container_size_type_ids = record.mapped('container_size_type').ids

                moves = self.env['move.out'].search([
                    ('location_id', 'in', container_yard_ids),
                    ('type_size_id', 'in', container_size_type_ids),
                    ('delivery_order_id', '=', record.delivery_id.id)
                ])
                moves_in = self.env['move.in'].search([
                    ('location_id', 'in', container_yard_ids),
                    ('type_size_id', 'in', container_size_type_ids),
                    ('do_no_id', '=', record.delivery_id.id)
                ])
                if moves:
                    type_size_count = {}
                    for move in moves:
                        type_size_id = move.type_size_id.id
                        if type_size_id in type_size_count:
                            type_size_count[type_size_id] += 1
                        else:
                            type_size_count[type_size_id] = 1

                        record.count = type_size_count.get(record.container_size_type.id, 0)
                elif moves_in:
                    type_size_count = {}
                    for move in moves_in:
                        type_size_id = move.type_size_id.id
                        if type_size_id in type_size_count:
                            type_size_count[type_size_id] += 1
                        else:
                            type_size_count[type_size_id] = 1

                        record.count = type_size_count.get(record.container_size_type.id, 0)

    def view_records(self):
        for record in self:
            if record.delivery_id:
                container_yard_ids = record.mapped('container_yard').ids
                container_size_type_ids = record.mapped('container_size_type').ids

                # Initialize variables for context
                related_moves_ids = []
                related_moves_in_ids = []

                # Process move.out records if they exist
                move_out_moves = self.env['move.out'].search([
                    ('location_id', 'in', container_yard_ids),
                    ('type_size_id', 'in', container_size_type_ids),
                    ('delivery_order_id', '=', record.delivery_id.id)
                ])
                if move_out_moves:
                    matching_move_out_moves = move_out_moves.filtered(
                        lambda m: m.type_size_id.id in container_size_type_ids
                    )
                    record.related_moves = matching_move_out_moves
                    related_moves_ids = matching_move_out_moves.ids

                # Process move.in records if they exist
                move_in_moves = self.env['move.in'].search([
                    ('location_id', 'in', container_yard_ids),
                    ('type_size_id', 'in', container_size_type_ids),
                    ('do_no_id', '=', record.delivery_id.id)
                ])
                if move_in_moves:
                    matching_move_in_moves = move_in_moves.filtered(
                        lambda m: m.type_size_id.id in container_size_type_ids
                    )
                    record.related_moves_in = matching_move_in_moves
                    related_moves_in_ids = matching_move_in_moves.ids

                # Prepare context based on what records are found
                context = {
                    'default_delivery_order_id': self.delivery_id,
                    'default_container_details': [(6, 0, self.delivery_id.container_details.ids)],
                }

                if related_moves_ids:
                    context['default_related_moves_ids'] = related_moves_ids
                if related_moves_in_ids:
                    context['default_related_moves_in'] = related_moves_in_ids

                return {
                    'name': _('View Allocations'),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'view.update.allocation.wizard',
                    'target': 'new',
                    'view_id': self.env.ref('empezar_delivery_order.view_allocation_wizard_form_view').id,
                    'context': context,
                }
