"""-*- coding: utf-8 -*-"""
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class ContainerDetails(models.Model):
    _name = "container.details.delivery"
    _description = "Container Details"
    _order = "create_date desc"

    delivery_id = fields.Many2one("delivery.order", string="Container Details", ondelete="cascade")
    container_qty = fields.Integer(string="Quantity", required=True, size=3)
    balance_container = fields.Integer(string="Balance", readonly=True)
    container_size_type = fields.Many2one("container.type.data", string="Container Type/Size",
                                          required=True)
    container_yard = fields.Many2one('container.facilities', string='Yard',
                                     domain=[('facility_type', '=', 'empty_yard')])
    quantity = fields.Integer(string="Deduct Quantity")
    # delivery_id = fields.Many2one("delivery.order", string="Container Details", ondelete="cascade")
    container_size_type_domain = fields.Char(string="Container Size Type Domain", compute="_compute_container_size_type_domain")
    edit_container_qty = fields.Boolean(compute='_compute_edit_container_qty', string="Can Edit Quantity", store=False)

    @api.constrains('container_size_type')
    def _check_unique_container_type(self):
        """if Check unique container_size_type is or not
           :return:
        """
        for container in self:
            if container.container_size_type:
                duplicate_containers = self.search([
                    ('id', '!=', container.id),
                    ('delivery_id', '=', container.delivery_id.id),
                    ('container_size_type', '=', container.container_size_type.id)
                ])

                if duplicate_containers:
                    raise ValidationError(_("Container Type/Size cannot entered multiple times."))

    @api.constrains('container_qty')
    def _check_container_qty(self):
        """check container_qty is valid or not
           :return:
        """
        for record in self:
            if not 1 <= record.container_qty <= 999:
                raise ValidationError(_('Container Quantity must be between 1 and 999.'))

    @api.model
    def create(self, vals):
        try:
            if 'container_qty' in vals:
                vals['balance_container'] = vals['container_qty']
        except Exception as e:
        # Log the error if needed
            _logger.error('Error while writing record: %s', e)
        return super(ContainerDetails, self).create(vals)


    @api.model
    def write(self, vals):
        try:
            # If container_qty is being updated, update balance_container as well
            if 'container_qty' in vals:
                for record in self:
                    # Ensure that balance_container follows container_qty
                    record.balance_container = vals['container_qty']

        except Exception as e:
            # Log the error if needed
            _logger.error('Error while writing record: %s', e)
        # Return result after the exception handling
        return  super(ContainerDetails, self).write(vals)

    container_details = fields.One2many("container.details", "delivery_id", string="Container Details")

    @api.depends('delivery_id.shipping_line_id', 'delivery_id.location','container_size_type')
    def _compute_container_size_type_domain(self):
        for record in self:
            if not record.delivery_id.location:
                raise ValidationError(_("Please select at least one Location."))
            elif not record.delivery_id.shipping_line_id:
                raise ValidationError(_("Please select at least one Shipping Line."))

            location_ids = record.delivery_id.location.ids
            shipping_mappings = self.env['location.shipping.line.mapping'].search([
                ('company_id', 'in', location_ids),
                ('shipping_line_id', '=', record.delivery_id.shipping_line_id.id)
            ])
            refer_container_values = set()
            for mapping in shipping_mappings:
                refer_container_values.add(mapping.refer_container)

            if 'yes' in refer_container_values and 'no' in refer_container_values:
                domain = [('is_refer', '=', 'yes')]
            elif 'yes' in refer_container_values:
                domain = [('is_refer', '=', 'yes')]
            elif 'no' in refer_container_values:
                domain = [('is_refer', '=', 'no')]
            else:
                domain = [('is_refer', 'in', ['yes', 'no'])]

            # Check for location changes
            previous_location = record._origin.delivery_id.location
            if previous_location != record.delivery_id.location:
                # Reset container size types if location has changed
                record.container_details = [(5, 0, 0)]

            record.container_size_type_domain = str(domain)

    @api.depends('container_qty', 'balance_container')
    def _compute_edit_container_qty(self):
        for record in self:
            if record.container_qty == record.balance_container:
                record.edit_container_qty = True
            else:
                record.edit_container_qty = False

    @api.model
    def unlink(self):
        """Override unlink to prevent deletion of container details based on quantity and balance."""
        for rec in self:
            # Check if container_qty is not equal to balance
            if rec.container_qty != rec.balance_container:
                raise ValidationError(
                    _("You cannot delete the records because this Container Size Type is already used."))

        # Call the original unlink method if validation passes
        return super(ContainerDetails, self).unlink()

