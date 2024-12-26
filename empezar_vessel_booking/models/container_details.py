# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class ContainerDetails(models.Model):
    _name = "container.details"
    _description = "Container Details"

    booking_id = fields.Many2one("vessel.booking", string="Container Details", ondelete='cascade')
    delivery_id = fields.Many2one("container.details.delivery", string="Container Details", ondelete="cascade")
    container_qty = fields.Integer(string="Quantity", required=True, size=3)
    balance = fields.Integer(string="Balance")
    container_size_type = fields.Many2one("container.type.data", string="Container Type/Size", required=True)
    refer_container_selection = fields.Char(related='booking_id.refer_container_selection')

    @api.model
    def create(self, vals):
        try:
            if 'container_qty' in vals:
                vals['balance'] = vals['container_qty']
        except Exception as e:
            # Log the error if needed
            _logger.error('Error while writing record: %s', e)
        return super(ContainerDetails, self).create(vals)

    @api.model
    def write(self, vals):
        try:
            # Check if 'container_qty' is being updated
            if 'container_qty' in vals:
                for record in self:
                    # Update balance only if it matches the current container_qty
                    if record.container_qty == record.balance:
                        record.balance = vals['container_qty']
        except Exception as e:
            # Log the error if needed
            _logger.error('Error while writing record: %s', e)
        # Call the parent method to continue the write operation
        return super(ContainerDetails, self).write(vals)

    @api.constrains('container_size_type')
    def _check_unique_container_type(self):
        """
            if Check unique container_size_type is or not
        """
        for container in self:
            if container.container_size_type:
                duplicate_containers = self.search([
                    ('id', '!=', container.id),
                    ('booking_id', '=', container.booking_id.id),
                    ('container_size_type', '=', container.container_size_type.id)
                ])
                if duplicate_containers:
                    raise ValidationError("Container Type/Size cannot be entered multiple times.")

    @api.constrains('container_qty')
    def _check_container_qty(self):
        for record in self:
            if not 1 <= record.container_qty <= 999:
                raise ValidationError(_('Container Quantity must be between 1 and 999.'))
