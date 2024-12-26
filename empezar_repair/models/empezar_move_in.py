from odoo import models, api

class MoveIn(models.Model):
    _inherit = "move.in"
    """Inherit the move in model to create a repair pending record"""

    @api.model
    def create(self, vals):
        """ Create the move in record"""

        move_in_record = super().create(vals)
        repair_operation = move_in_record.location_id.operations_ids.mapped('name')
        if 'Repair' in repair_operation and 'Gate Operations' in repair_operation:
            for shipping_mapping in move_in_record.location_id.shipping_line_mapping_ids:
                if shipping_mapping.shipping_line_id.id == move_in_record.shipping_line_id.id:
                    if shipping_mapping.repair == 'yes':

                        # Create a corresponding repair pending record
                        self.env['repair.pending'].create({
                            'move_in_id': move_in_record.id,
                            'shipping_line_logo':move_in_record.shipping_line_logo,
                            'shipping_line_id': move_in_record.shipping_line_id.id,
                            'location_id': move_in_record.location_id.id,
                            'container_no': move_in_record.container,
                            'type_size_id': move_in_record.type_size_id.id,
                            'move_in_date_time': move_in_record.move_in_date_time,
                            'month': move_in_record.month,
                            'year': move_in_record.year,
                            'grade': move_in_record.grade,
                            'gross_wt': move_in_record.gross_wt,
                            'tare_wt': move_in_record.tare_wt,
                            'damage_condition': move_in_record.damage_condition.id,
                        })
        return move_in_record
