from odoo import models, _
from odoo.exceptions import ValidationError


class ContainerMaster(models.Model):
    _inherit = "container.master"

    def action_view_history(self):
        """ Method to view history of the containers"""
        move_out_invoices = self.env['pending.invoices'].search(
            [('container_number', '=', self.name), ('movement_type', '=', 'move_out')],
            order='id DESC'
        )

        move_in_invoices = self.env['pending.invoices'].search(
            [('container_number', '=', self.name), ('movement_type', '=', 'move_in')],
            order='id DESC'
        )

        if not move_out_invoices and not move_in_invoices:
            raise ValidationError(_("No history found"))

        linked_move_in_ids = set()
        results = []

        for invoice in move_out_invoices:
            move_out_record = invoice.move_out_id
            location_name = invoice.location_id.name
            move_out_date_time = move_out_record.move_out_date_time

            # Generate the move out URL
            move_out_url = None
            if move_out_record:
                move_out_url = (f'<a href="/web#id={move_out_record.id}&model=move.out&view_type=form"'
                                f' target="_blank"><i class="fa fa-arrow-right"></i></a>') \
                    if move_out_record else None


            # Add move_in details if linked to the move_out
            move_in_record = move_out_record.move_in_id
            move_in_date_time = move_in_record.move_in_date_time if move_in_record else None
            move_in_url = (f'<a href="/web#id={move_in_record.id}&model=move.in&view_type=form" '
                           f'target="_blank"><i class="fa fa-arrow-right"></i></a>') \
                if move_in_record else None

            results.append({
                'location_id': location_name,
                'move_out_date_time': move_out_date_time,
                'move_out_url': move_out_url,
                'move_in_date_time': move_in_date_time,
                'move_in_url': move_in_url,
            })

            # Track the move_in records linked to move_outs to avoid duplicates
            if move_in_record:
                linked_move_in_ids.add(move_in_record.id)

        # Append move_in records that are not linked to any move_out
        for invoice in move_in_invoices:
            move_in_record = invoice.move_in_id
            if move_in_record.id not in linked_move_in_ids:
                location_name = invoice.location_id.name
                move_in_date_time = move_in_record.move_in_date_time
                move_in_url = (f'<a href="/web#id={move_in_record.id}&model=move.in&view_type=form"'
                               f' target="_blank"><i class="fa fa-arrow-right"></i></a>') \
                    if move_in_record else None

                results.append({
                    'location_id': location_name,
                    'move_out_date_time': None,
                    'move_out_url': None,
                    'move_in_date_time': move_in_date_time,
                    'move_in_url': move_in_url,
                })

        # Return the history view with the results
        return {
            'type': 'ir.actions.act_window',
            'name': _('Move History - %s') % self.name,
            'res_model': 'container.history.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_history_line_ids': results
            },
        }
