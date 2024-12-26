from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import logging

# Set up the logger
_logger = logging.getLogger(__name__)


class UpdateAllocationWizard(models.Model):
    _name = 'update.allocation.wizard'

    container_yard = fields.Many2one(
        'container.facilities', string='Yard', domain=[('facility_type', '=', 'empty_yard')])
    quantity = fields.Integer(string="Deduct Quantity")
    delivery_order_id = fields.Many2one('delivery.order', string='Delivery Order')
    container_details = fields.One2many(related='delivery_order_id.container_details', readonly=False)
    container_size_type = fields.Many2one(
        "container.type.data",
        string="Container Type/Size")
    container_size_type_domain = fields.Char(string="Container Type/Size Domain", compute='compute_container_type_domain')

    @api.constrains('quantity')
    def _check_quantity(self):
        for rec in self:
            if not (1 <= rec.quantity <= 999):
                raise ValidationError(_("The quantity must be between 1 and 999."))

    @api.depends('container_size_type')
    def compute_container_type_domain(self):
        for rec in self:
            # Ensure only a single record is considered for container_details
            container_details = rec.delivery_order_id.container_details
            if container_details:
                # Fetch all container_size_type values from container.details.delivery
                container_sizes = self.env['container.details.delivery'].search([
                    ('container_size_type', 'in', container_details.mapped('container_size_type').ids)
                ]).mapped('container_size_type')

                # Check if any container size types were found
                if container_sizes:
                    # Generate domain with all the container_size_types found
                    rec.container_size_type_domain = str([('id', 'in', container_sizes.ids)])
                else:
                    rec.container_size_type_domain = str([])
            else:
                rec.container_size_type_domain = str([])

    def action_update_allocation(self):
        """
        Updates the allocation by adjusting container balances and creating
        or updating related records in view.update.allocation.wizard.
        """
        for detail in self.container_details:
            # Match container_size_type
            if detail.container_size_type == self.container_size_type:
                if detail.balance_container is None or self.quantity is None:
                    continue

                balance = detail.balance_container - self.quantity
                if balance < 0:
                    raise ValidationError(
                        _("Entered quantity exceeds balance quantity for container type: %s.")
                        % detail.container_size_type.name
                    )

                # Update balance_container and yard
                detail.write({
                    'balance_container': balance,
                    'container_yard': self.container_yard.id
                })

                active_ids = self.env.context.get('active_ids', [])

                if active_ids:
                    # Refine the search to prevent duplicates based on the unique combination of fields
                    existing_allocation = self.env['view.update.allocation'].search([
                        ('delivery_order_id', '=', self.delivery_order_id.id),
                        ('container_type_size', '=', detail.container_size_type.name),
                        ('yard', '=', self.container_yard.name),
                        ('is_from_location', '=', False),  # Only look for allocations where is_from_location is False
                    ])

                    if existing_allocation:
                        # If allocation exists with is_from_location=False, update the count
                        for allocation in existing_allocation:
                            updated_count = allocation.count + self.quantity
                            allocation.write({'count': updated_count})

                    else:
                        # Create a new allocation record for this unique combination
                        self.env['view.update.allocation'].create({
                            'delivery_order_id': self.delivery_order_id.id,
                            'container_type_size': detail.container_size_type.name,
                            'yard': self.container_yard.name,
                            'count': self.quantity,
                            'is_from_location': False,
                        })

        _logger.info("Allocation updated successfully for Delivery Order ID: %s", self.delivery_order_id.id)
