from odoo import models, api, fields, _
from odoo.exceptions import ValidationError

class DeliveryOrder(models.Model):
    _inherit = "delivery.order"

    is_delivery_in_move_out = fields.Boolean("Is Move out", compute="_compute_delivery_order_in_move_out", default=False)
    quantity = fields.Integer("Quantity")


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

    @api.constrains('active')
    def _check_delivery_active_constraint(self):
        """Ensures that if there is an existing Move Out record, the active field is set to False."""
        for record in self:
            if record.delivery_no:
                if not record.active:
                    # Check if there's an active record with the same delivery_no and not this record
                    move_out_records = self.env['move.out'].search([
                        ('active', '=', True),
                        ('delivery_order_id', '=', record.delivery_no),
                    ])
                    move_in_records = self.env['move.in'].search([
                        ('active', '=', True),
                        ('do_no_id', '=', record.delivery_no),
                    ])
                    if move_out_records:
                        raise ValidationError(_("Cannot archive a record Delivery Number already exist in Move out."))
                    if move_in_records:
                        raise ValidationError(_("Cannot archive a record Delivery Number already exist in Move in."))

    @api.depends('container_details.delivery_id')
    def _compute_delivery_order_in_move_out(self):
        """Check if the delivery order number exists in the move.out model."""
        for record in self:
            move_out_records = self.env['move.out'].search_count([('delivery_order_id', '=', record.container_details.delivery_id.id)])
            if move_out_records > 0:
                record.is_delivery_in_move_out = True
            else:
                record.is_delivery_in_move_out = False

    def view_allocations(self):
        # Case when move_out_record exists
        move_out_records = self.env['move.out'].search([('delivery_order_id', '=', self.id)])
        for move_out_record in move_out_records:
            # Loop through container_details to compare container_type_size with move_out record
            for container_detail in self.container_details:

                if move_out_record.type_size_id.name == container_detail.container_size_type.name:
                    # If they match, proceed to create or update the allocation record
                    container_type = move_out_record.type_size_id.name
                    location = move_out_record.location_id.name
                    container_type_count = self.env['move.out'].search([
                        ('delivery_order_id', '=', self.id),
                        ('type_size_id', '=', move_out_record.type_size_id.id),
                        ('location_id', '=', move_out_record.location_id.id)
                    ])

                    # Check if the allocation already exists in view.update.allocation.wizard
                    existing_allocation = self.env['view.update.allocation'].search([
                        ('delivery_order_id', '=', self.id),
                        ('container_type_size', '=', container_type),
                        ('yard', '=', location),
                        ('is_from_location','=',True)
                    ])
                    if existing_allocation:
                            updated_count = existing_allocation.count + self.quantity
                            existing_allocation.write({'count': updated_count})



                    move_out_list = container_type_count.ids

                    if existing_allocation:
                        # If allocation exists, accumulate the count
                        existing_allocation.write({
                            'count': len(container_type_count),
                            'related_moves_ids': move_out_list
                        })
                    else:
                        # Create a new record in view.update.allocation.wizard
                        self.env['view.update.allocation'].create({
                            'delivery_order_id': self.id,
                            'container_type_size': container_type,
                            'yard': location,
                            'count': len(container_type_count),
                            'is_from_location': True,
                            'related_moves_ids': move_out_list
                        })
        move_in_records = self.env['move.in'].search([('do_no_id', '=', self.id)])

        for move_in_record in move_in_records:
            # Loop through container_details to compare container_type_size with move_in record
            for container_detail in self.container_details:
                if move_in_record.type_size_id.name == container_detail.container_size_type.name:
                    # If they match, proceed to create or update the allocation record
                    container_type = move_in_record.type_size_id.name
                    location = move_in_record.location_id.name
                    container_type_count = self.env['move.in'].search([
                        ('do_no_id', '=', self.id),
                        ('type_size_id', '=', move_in_record.type_size_id.id),
                        ('location_id', '=', move_in_record.location_id.id),

                    ])

                    # Check if the allocation already exists in view.update.allocation.wizard
                    existing_allocation = self.env['view.update.allocation'].search([
                        ('delivery_order_id', '=', self.id),
                        ('container_type_size', '=', container_type),
                        ('yard', '=', location),
                        ('is_from_location', '=', True)
                    ])
                    if existing_allocation:
                        # Update the count field by adding the new quantity to the existing count
                        updated_count = existing_allocation.count + self.quantity
                        existing_allocation.write({'count': updated_count})


                    move_in_list = container_type_count.ids

                    if existing_allocation:
                        # If allocation exists, accumulate the count
                        existing_allocation.write({
                            'count': len(container_type_count),
                            'related_moves_in': move_in_list
                        })
                    else:
                        # Create a new record in view.update.allocation.wizard
                        self.env['view.update.allocation'].create({
                            'delivery_order_id': self.id,
                            'container_type_size': container_type,
                            'yard': location,
                            'count': len(container_type_count),
                            'is_from_location': True,
                            'related_moves_in': move_in_list
                        })

        # After updating/creating allocations, return action to show the updated records in the tree view
        return {
            'name': _('View Allocations'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'domain': [('delivery_order_id', '=', self.id)],
            'res_model': 'view.update.allocation',
            'target': 'current',  # This will show the records in the current window
            'view_id': self.env.ref('empezar_delivery_order.view_allocation_wizard_tree_view').id,

            'context': {
                'default_delivery_order_id': self.id,
            },
        }
