# -*- coding: utf-8 -*-
import io
import re
import os
import base64
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import pandas as pd

import logging

_logger = logging.getLogger(__name__)


class EnableProfilingWizard(models.TransientModel):
    _name = 'booking.import.wizard'
    _description = "Upload Containers"

    file = fields.Binary('Upload Containers')
    file_namex = fields.Char('Binary Name')
    delimiter = fields.Char('Delimiter', default=',')
    my_file = fields.Char('name')
    is_import_done = fields.Boolean(default=False)
    is_download = fields.Boolean(default=False)
    vessel_booking_id = fields.Many2one('vessel.booking', string='Vessel Booking',
                                        default=lambda self: self.env.context.get('active_id'))

    @api.onchange('file')
    @api.constrains('file')
    def _check_file_type(self):
        """
            This method validates the uploaded shipping logo:
            **Raises:**
                ValidationError:
                ->If the uploaded file is not .xls/.xlsx
                ->If the uploaded logo size exceeds 1MB.
        """
        if self.file:
            # Get the file name and check the extension
            file_name = self.file_namex
            if not file_name.lower().endswith(('.xls', '.xlsx')):
                raise ValidationError("File Type selected is not allowed. Please upload files of types - .xls / .xlsx.")
            if len(self.file) > 5 * 1024 * 1024:
                raise ValidationError("File size cannot exceed 5MB.")

    def action_import(self):
        """
        This method validates the uploaded containers
        """
        self.ensure_one()
        if self.file:
            self.check_header_files_validations()
            # Read data from the uploaded Excel file
            excel_file = base64.b64decode(self.file)
            df = pd.read_excel(io.BytesIO(excel_file))

            container_numbers = df['Container Number'].tolist()

            if 'Container Number' not in df.columns:
                raise ValidationError("Invalid Excel Header")

            self.validate_container_number(df)
            self.container_number_quantity(df)

            for container_number in container_numbers:
                if not pd.isna(container_number) and not container_number.strip() == '':
                    container = self.env['container.master'].search([('name', '=', container_number)])
                    code = container.type_size.company_size_type_code
                    container_name_code = f"{container.name} ({code})"
                    self.env['container.number'].create({
                        'name': container_name_code,
                        'vessel_booking_id': self.env.context.get('active_id'),
                    })

        return {
            'type': 'ir.actions.act_window_close',
            'tag': 'reload',
        }

    def check_header_files_validations(self):
        """ compare sample file and uploaded file header if different then
            it will raise validation error.
            :return:
        """
        # Get the base path of the module
        module_base_path = os.path.dirname(os.path.dirname(__file__))

        # Construct the file path relative to the module's directory

        file_relative_path = 'static/src/document/Container_Booking.xlsx'
        sample_file_path = os.path.join(module_base_path, file_relative_path)

        # Check if the sample file exists
        if not os.path.exists(sample_file_path):
            raise ValidationError(_('The specified sample Excel file does not exist.'))

        # Read the sample Excel file to get its columns
        sample_df = pd.read_excel(sample_file_path)
        sample_file_columns = sample_df.columns.tolist()

        # Check if an upload file is provided
        if not self.file:
            raise ValidationError(_('No container file uploaded.'))

        # Read the uploaded Excel file
        file_content = base64.b64decode(self.file)
        # file_content = pd.read_excel(self.upload_file)
        df = pd.read_excel(io.BytesIO(file_content))
        upload_file_columns = df.columns.tolist()

        # Compare headers
        if sample_file_columns != upload_file_columns:
            raise ValidationError(_('Invalid columns headers in the file uploaded'))

        return True

    @api.model
    def validate_container_number(self, df):
        """
            this Method is used for check container number validation
        """
        invalid_container_number = []
        for index,row in df.iterrows():
            container_number = row.get('Container Number')
            if not pd.isna(container_number) and not container_number.strip() == '':
                if isinstance(container_number, (float, int)):
                    container_number = str(container_number)
                if len(container_number) != 11:
                    raise ValidationError(f"Invalid container number {container_number}: must be 11 characters.")
                if not re.match(r'^[A-Z]{3}U[0-9]{7}$', container_number):
                    raise ValidationError(f"Invalid container number {container_number}: format must be XXXU9999999.")
                if not self.env['container.inventory'].search([('name', '=', container_number),
                                                               ('location_id', 'in', self.vessel_booking_id.location.ids)]):
                    invalid_container_number.append(container_number)
            else:
                pass
        if invalid_container_number:
            error_message = "Container Number is not present in the inventory of the location"
            raise ValidationError(error_message)

    def container_number_on_booking(self, container_numbers):
        """
            this Method is used for check container number is present in other booking record or not
        """
        booking_id = self.env.context.get('active_id')
        vessel_booking_model = self.env['vessel.booking']

        for rec in container_numbers:
            container = self.env['container.master'].search([('name', '=', rec)])
            code = container.type_size.company_size_type_code
            container_record = f"{container.name} ({code})"
            if rec and rec != '' and not pd.isna(rec):
                existing_container_numbers = vessel_booking_model.search([
                    ('id', '!=', booking_id),
                    ('rec_status', '=', 'active'),  # Check for active records
                    ('container_numbers.name', '=', container_record)
                ])
                # If existing bookings are found
                if existing_container_numbers:
                    # Iterate through existing bookings
                    for booking in existing_container_numbers:
                        # Debugging: Log the current booking being checked
                        _logger.debug(f"Checking booking: {booking.booking_no} for container {container_record}")
                        # Iterate over the container numbers in the existing booking
                        for containers in booking.container_numbers:
                            if containers.name == container_record:  # Ensure we are matching the correct container number
                                if containers.unlink_reason or containers.move_out_datetime:
                                        _logger.debug(f"Skipping validation for container {containers.name} due to unlink_reason")
                                else:
                                    # If the container doesn't have an unlink_reason, raise validation
                                    booking_numbers = existing_container_numbers.mapped('booking_no')
                                    raise ValidationError(
                                        f'Container number {rec} already present in the Vessel Booking(s): {booking_numbers}')

    def container_number_quantity(self, df):
        self.ensure_one()
        """
            this Method is used for check container number quantity
        """
        # Get all container numbers from the excel file
        container_numbers = df['Container Number'].tolist()
        container_details_type_data = []
        container_numbers_type_date = []
        excel_file_container_type_data = []

        self.container_number_on_booking(container_numbers)

        if container_numbers != '':
            unique_container_numbers = set()
            for container_number in container_numbers:
                if not pd.isna(container_number) and not container_number.strip() == '':
                    if container_number in unique_container_numbers:
                        raise ValidationError(
                            _("Please enter unique container numbers. Duplicate found: %s" % container_number))
                    unique_container_numbers.add(container_number)

            existing_numbers = self.env['container.number'].search([
                ('vessel_booking_id', '=', self._context.get('active_id'))
            ]).mapped('name')
            main_parts = [cn.split(' ')[0] for cn in existing_numbers]
            existing_container_numbers = set(main_parts)
            # Check for duplicates
            duplicate_numbers = set(container_numbers) & set(existing_container_numbers)
            if duplicate_numbers:
                raise ValidationError(
                    _(f'Container number(s) {", ".join(duplicate_numbers)} already exist in Container No.'))

            # Get all container types/sizes and their quantities from container details.
            container_details = self.env['vessel.booking'].browse(self._context.get('active_id')).container_details
            for detail in container_details:
                container_details_type_data.append({
                    'container_size_type': detail.container_size_type.id,
                    'container_qty': detail.container_qty
                })
            # Get all the container type/sizes and their quantities from container numbers.
            container_number_details = self.env['vessel.booking'].browse(
                self._context.get('active_id')).container_numbers.mapped('name')
            for rec in container_number_details:
                main_parts = [str(rec).split(' ')[0]]
                get_container_number = self.env['container.master'].search([('name', 'in', main_parts)])
                for type_size in get_container_number.type_size:
                    container_numbers_type_date.append(type_size.id)

            if container_details_type_data:
                for rec in container_numbers:
                    if rec and rec != '' and not pd.isna(rec):
                        main_parts = [str(rec).split(' ')[0]]
                        container_inventory = self.env['container.master'].search([('name', 'in', main_parts)])
                        excel_file_container_type_data.append(container_inventory.mapped('type_size.id'))

                    self.container_detail_check(container_numbers, container_details_type_data)

                for rec in container_details_type_data:
                    count = 0
                    size_type_id = rec.get('container_size_type')
                    size_type_obj = self.env['container.type.data'].browse(size_type_id).exists()
                    size_type_quantity = rec.get('container_qty')
                    flattened_excel_data = [item for sublist in excel_file_container_type_data for item in sublist]

                    if container_numbers_type_date and size_type_id in container_numbers_type_date:
                        count = container_numbers_type_date.count(size_type_id)
                    if flattened_excel_data and size_type_id in flattened_excel_data:
                        type_count = flattened_excel_data.count(size_type_id)
                        type_count += count
                        if type_count > size_type_quantity:
                            raise ValidationError(
                                _(f'Container numbers added exceed the container type/size ({(size_type_obj.name)}) details.'))


    def container_detail_check(self, container_numbers, container_details_type_data):
        """
            This method validates the uploaded containers Number Based on Each Container Type
        """
        existing_container_types = [detail['container_size_type'] for detail in container_details_type_data]
        # Check if each container number in the Excel file is valid
        for container_number in container_numbers:
            container_master = self.env['container.master'].search([('name', '=', container_number)])
            if container_master:
                container_size_id = container_master.type_size.id
                if container_size_id not in existing_container_types:
                    raise ValidationError(
                        _(f'Container number {container_number} has a type/size ({container_master.type_size.name}) not present in container details.'))
