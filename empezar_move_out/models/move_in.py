# -*- coding: utf-8 -*-
import re
import pytz
from pytz import timezone
from datetime import datetime
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class MoveIn(models.Model):

    _inherit = "move.in"

    do_no_compute_domain = fields.Many2many('delivery.order', string="DO/No Domain",
                                            compute="_compute_do_no_domain")
    booking_no_compute_domain = fields.Many2many('vessel.booking', string="Booking Domain",
                                                 compute="_compute_booking_no_domain")

    @api.constrains('move_in_date_time')
    def _move_in_date_time(self):
        ist = pytz.timezone('Asia/Kolkata')
        for record in self:
            if record.move_in_date_time:
                move_in_date_time_ist = record.move_in_date_time.astimezone(ist)
                move_in_date = move_in_date_time_ist.date()
                current_hour = move_in_date_time_ist.hour
                current_minute = move_in_date_time_ist.minute
            else:
                move_in_date = None
                current_hour = None
                current_minute = None

            inventory_model = self.env['container.inventory']
            inventory_model.with_context(active_test=False).search([
                ('move_in_id', '=', record.id),
            ], limit=1).write({
                'move_in_date': move_in_date,
                'hour': str(current_hour),
                'minutes': str(current_minute),
            })

    @api.depends('location_id', 'movement_type')
    def _compute_do_no_domain(self):
        """
        Compute the container number domain based on locations and
        move out records.
        """
        for record in self:
            if record.location_id and record.movement_type:
                if record.movement_type == 'factory_return':
                    get_do_numbers = self.env['delivery.order'].search([
                        ('location', '=', record.location_id.id),
                        ('active', '=', True)
                    ]).ids
                    record.do_no_compute_domain = [(6, 0, get_do_numbers)]
                else:
                    get_do_numbers = self.env['delivery.order'].search([('location', 'in', [record.location_id.id]),
                                                                        ('active', '=', True)]).ids
                    move_out_do_numbers = (self.env['move.out'].search([('movement_type', '=', 'export_stuffing')]).
                                           mapped('delivery_order_id').ids)
                    allow_ids = list(set(get_do_numbers) - set(move_out_do_numbers))
                    record.do_no_compute_domain = [(6, 0, allow_ids)]
            else:
                record.do_no_compute_domain = []

    @api.depends('location_id')
    def _compute_booking_no_domain(self):
        """
        Compute the booking no domain based on the
        move in locations.
        """
        for record in self:
            if record.location_id:
                get_booking_numbers = self.env['vessel.booking'].search(
                    [('location', 'in', [record.location_id.id]),
                     ('active', '=', True)]).ids
                move_out_booking_numbers = (
                    self.env['move.out'].search([('movement_type', '=', 'repo')]).
                    mapped('booking_no_id').ids)
                allow_ids = list(set(get_booking_numbers) - set(move_out_booking_numbers))
                record.booking_no_compute_domain = [(6, 0, allow_ids)]
            else:
                record.booking_no_compute_domain = []

    @api.constrains('container')
    def _check_container(self):
        container_model = self.env['container.master']
        inventory_model = self.env['container.inventory']
        ist = pytz.timezone('Asia/Kolkata')

        for record in self:
            if record.move_in_date_time:
                move_in_date_time_ist = record.move_in_date_time.astimezone(ist)
                move_in_date = move_in_date_time_ist.date()
                current_hour = move_in_date_time_ist.hour
                current_minute = move_in_date_time_ist.minute
            else:
                move_in_date = None
                current_hour = None
                current_minute = None
            container_number = record.container
            existing_container = container_model.search([('name', '=', container_number)],
                                                        limit=1)
            existing_inventory = inventory_model.search([('name', '=', container_number),('location_id', '=', record.location_id.id)],
                                                        limit=1)
            record.is_valid_container_number()
            if record.movement_type == 'factory_return':
                if not existing_container:
                    raise ValidationError(_("Movement type - Factory Return not applicable for this container as it was not moved out from here"))
            if not existing_container and container_number and not existing_inventory :
                container_master_id = container_model.create({
                    'name': container_number,
                    'shipping_line_id': record.shipping_line_id.id,
                    'type_size': record.type_size_id.id,
                    'month': record.month,
                    'year': record.year,
                    'gross_wt': record.gross_wt,
                    'tare_wt': record.tare_wt,
                })
                if container_master_id:
                    inventory_model.create({
                        'grade': record.grade,
                        'damage_condition':record.damage_condition.id,
                        'container_master_id': container_master_id.id,
                        'move_in_id':record.id,
                        'name': container_number,
                        'location_id': record.location_id.id,
                        'status':'ae',
                        'move_in_date': move_in_date,
                        'hour': str(current_hour),
                        'minutes': str(current_minute),
                    })

            elif existing_container and not existing_inventory:
                inventory_model.create({
                    'grade': record.grade,
                    'damage_condition': record.damage_condition.id,
                    'container_master_id': existing_container.id,
                    'move_in_id': record.id,
                    'name': container_number,
                    'location_id': record.location_id.id,
                    'status': 'ae',
                    'move_in_date': move_in_date,
                    'hour': str(current_hour),
                    'minutes': str(current_minute),
                })
            elif existing_container and existing_inventory:
                existing_inventory.write({
                    'grade': record.grade,
                    'damage_condition': record.damage_condition.id,
                    'container_master_id': existing_container.id,
                    'move_in_id': record.id,
                    'name': container_number,
                    'location_id': record.location_id.id,
                    'move_in_date': move_in_date,
                    'hour': str(current_hour),
                    'minutes': str(current_minute),
                })

    @api.onchange('container')
    @api.depends('container')
    def check_container_number_validations(self):
        """
        Container number validations.
        """
        self.ensure_one()

        self.is_valid_container_number()

        self.populate_seal_numbers()

        if not self.container:
            return

        # Search for the container from container master.
        master_data = self.env['container.master'].search([
            ('name', '=', self.container)
        ], limit=1)
        inventory_data = self.env['container.inventory'].search([
            ('name', '=', self.container)
        ], limit=1)
        if self.container:
            self.container = self.container.upper()
        # if not master_data:
        #     raise ValidationError(_('This container number is not available in inventory'))

        if not self.location_id:
            return

        container_shipping_line_id = master_data.shipping_line_id
        container_type_size = master_data.type_size.id
        if container_type_size:
            type_size_obj = self.env['container.type.data'].browse(container_type_size).exists()
            if type_size_obj and type_size_obj.is_refer == 'no':
                raise ValidationError(
                    _("No refer containers are allowed to be moved in %s") % self.location_id.name)

        # Fetch all relevant shipping lines for the location
        location_shipping_lines = self.location_id.shipping_line_mapping_ids.mapped(
            'shipping_line_id')

        if container_shipping_line_id not in location_shipping_lines:
            return

        # Search once for the location's shipping line mappings
        mapping_shipping_line_obj = self.env['location.shipping.line.mapping'].search([
            ('company_id', '=', self.location_id.id),
            ('shipping_line_id', '=', container_shipping_line_id.id)
        ], limit=1)

        if not mapping_shipping_line_obj:
            return

        # Check for the condition in the mapped shipping line object
        if 'Move In' in mapping_shipping_line_obj.gate_pass_ids.mapped('name') and \
                mapping_shipping_line_obj.refer_container == 'no':
            raise ValidationError(
                _("No refer containers are allowed to be moved in %s") % self.location_id.name)
        else:
            # self.grade = inventory_data.grade
            # self.damage_condition = inventory_data.damage_condition
            self.shipping_line_id = master_data.shipping_line_id
            self.type_size_id = master_data.type_size
            self.month = master_data.month
            self.year = master_data.year
            self.gross_wt = master_data.gross_wt
            self.tare_wt = master_data.tare_wt
            self.container_status = inventory_data.status

    def populate_seal_numbers(self):
        """
        Populate seal number based on the movement type
        and container number.
        """
        if self.movement_type == 'factory_return' and self.container:
            container_id = self.env['container.master'].search([('name', '=', self.container)])
            get_latest_move_out = self.env['move.out'].search(
                [('container_id', '=', container_id.id)], order='id desc', limit=1)
            if get_latest_move_out:
                if get_latest_move_out.seal_no_1:
                    self.seal_no_1 = get_latest_move_out.seal_no_1.seal_number
                if get_latest_move_out.seal_no_2:
                    self.seal_no_2 = get_latest_move_out.seal_no_2.seal_number

    @api.onchange('movement_type')
    def onchange_movement_type(self):
        """
        Empty other records in movement type.
        :return:
        """
        self.ensure_one()
        if self.movement_type == 'import_destuffing':
            self.repo_from = False
            self.from_factory = False
            self.from_port = False
            self.from_terminal = False
            self.from_cfs_icd = False
            self.from_empty_yard = False
            self.from_factory = False
            self.booking_no_id = False
            self.do_no_id = False
            self.is_seal_return = False
        elif self.movement_type == 'repo':
            self.import_destuffing_from = False
            self.repo_from = False
            self.from_factory = False
            self.from_cfs_icd = False
            self.do_no_id = False
            self.is_seal_return = False
        else:
            self.import_destuffing_from = False
            self.repo_from = False
            self.from_factory = False
            self.from_cfs_icd = False
            self.from_port = False
            self.from_terminal = False
            self.from_empty_yard = False
            self.booking_no_id = False
            self.do_no_id = False

        self.populate_seal_numbers()

    # def write(self, vals):
    #     """
    #     Disable record validations.
    #     """
    #     res = super().write(vals)
    #     if 'active' in vals:
    #         self.check_validation()
    #     return res

    @api.constrains('container')
    def check_validation(self):
        """
        Check container validations based on move in &
        Move out records.
        :return:
        """
        for record in self:
            # Check for the uniqueness of the container_id
            container_id = self.env['container.master'].search([('name', '=', record.container)])
            existing_move_in = self.env['move.in'].search([
                ('container', '=', record.container), ('id', '!=', record.id)])
            if existing_move_in:
                existing_move_in_count = len(existing_move_in)
                existing_move_out = self.env['move.out'].search([
                    ('container_id', '=', container_id.id)
                ])
                existing_move_out_count = len(existing_move_out)
                if not existing_move_out:
                    raise ValidationError(
                        f"Container {container_id.name} cannot be moved in as it is already moved in {existing_move_in[0].location_id.name}")

                elif existing_move_out_count != existing_move_in_count:
                    raise ValidationError(
                        f"Container {container_id.name} cannot be moved in as it is already moved in {existing_move_in[0].location_id.name}")

            if record.do_no_id:
                delivery_order_id = self.env['delivery.order'].search(
                    [('id', '=', record.do_no_id.id)])
                if delivery_order_id:
                    matching_container_details = delivery_order_id.container_details.filtered(
                        lambda detail: detail.container_size_type == container_id.type_size)
                    if matching_container_details:
                        for container_detail in matching_container_details:
                            if record.movement_type == "import_destuffing":
                                container_detail.balance_container -= 1
                            elif record.movement_type == "factory_return":
                                container_detail.balance_container += 1
            elif record.booking_no_id:
                vessel_order_id = self.env['vessel.booking'].search(
                    [('id', '=', record.booking_no_id.id)])
                if vessel_order_id:
                    matching_container_details = vessel_order_id.container_details.filtered(
                        lambda detail: detail.container_size_type == container_id.type_size)
                    if matching_container_details:
                        for container_detail in matching_container_details:
                            if record.movement_type == "repo":
                                container_detail.balance -= 1


    def is_valid_container_number(self):
        if self.container:
            container_regex = r'^[A-Za-z]{4}[0-9]{7}$'
            if not re.match(container_regex, self.container):
                raise ValidationError(_("Container Number is invalid."))
            self.check_digit_validation_for_container()

    @api.model
    def get_edit_popup_message(self, move_in_id):
        """
        This method is called from js file to open edit pop-up conditionally.
        """
        if not move_in_id:
            return False

        move_in_obj = self.env['move.in'].browse(move_in_id)

        if not move_in_obj.exists():
            return False

        is_gate_pass_generated = False
        is_edi_generated = False
        is_damage_edi_generated = False

        shipping_line = move_in_obj.shipping_line_id
        location = move_in_obj.location_id

        # Check if there are any active shipping line mappings for the location
        mapped_shipping_lines = location.shipping_line_mapping_ids.filtered(
            lambda line: line.shipping_line_id == shipping_line and line.active
        )

        # Check if there are any active EDI settings for the location and shipping line
        mapped_move_in_location_edi = self.env['edi.settings'].search(
            [('location', '=', location.id), ('active', '=', True), ('shipping_line_id', '=', shipping_line.id),
             ('edi_type', '=', 'move_in')]
        )

        mapped_damage_location_edi = self.env['edi.settings'].search(
            [('location', '=', location.id), ('active', '=', True), ('shipping_line_id', '=', shipping_line.id),
             ('edi_type', '=', 'damaged')]
        )

        # Determine if gate pass has been generated
        if mapped_shipping_lines and any(
                'Move In' in line.gate_pass_ids.mapped('name') for line in mapped_shipping_lines):
            if move_in_obj.gate_pass_no:
                is_gate_pass_generated = True

        # Determine if EDI has been generated
        if mapped_move_in_location_edi and move_in_obj.is_edi_send:
            is_edi_generated = True

        # Determine if damage EDI has been generated
        if mapped_damage_location_edi and move_in_obj.is_damage_edi_send:
            is_damage_edi_generated = True

        # Return the result as a dictionary or other format as needed
        return {
            'is_gate_pass_generated': is_gate_pass_generated,
            'is_edi_generated': is_edi_generated,
            'is_damage_edi_generated': is_damage_edi_generated,
        }
