# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import openpyxl
import io, os
import base64
import pandas as pd
from datetime import datetime
from .upload_inventory_wizard import UploadInventoryWizard
import logging
_logger = logging.getLogger(__name__)

class UpdateContainerWizard(models.TransientModel):

    _name = "update.container.wizard"
    _description = "Update Container Status"

    file_name = fields.Char(string="File Name")
    location_id = fields.Many2one('res.company', string="Location", required=True, domain="[('parent_id','!=',False)]")
    upload_inventory_file = fields.Binary(string="Upload File",
                                          help="Only XLS or XLSX files with max size of 5 MB and"
                                                                        " having max 200 entries.",
                                          required=True, copy=False, exportable=False)
    
    def action_submit(self):
        """
        Check validations for uploaded excel files and create records in container master and upload inventory
        model if all validations pass.
        :return:
        """
        UploadInventoryWizard.check_file_type_and_size_validations(self)
        self.check_header_files_validations()
        self.check_require_columns_data()
        UploadInventoryWizard.check_data_length_validations(self)
        self.check_container_validations()
        self.check_status_validations()
        self.record_status_update_for_container_master()
        self.create_upload_container_status_record()

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def check_header_files_validations(self):
        """
        compare sample file and uploaded file header if different then it will raise validation error.
        :return:
        """
        # Get the base path of the module
        module_base_path = os.path.dirname(os.path.dirname(__file__))

        # Construct the file path relative to the module's directory
        file_relative_path = 'static/src/document/update_container_status_sample.xlsx'
        sample_file_path = os.path.join(module_base_path, file_relative_path)

        # Check if the sample file exists
        if not os.path.exists(sample_file_path):
            raise ValidationError(_('The specified sample Excel file does not exist.'))

        # Read the sample Excel file to get its columns
        sample_df = pd.read_excel(sample_file_path)
        sample_file_columns = sample_df.columns.tolist()

        # Check if an upload file is provided
        if not self.upload_inventory_file:
            raise ValidationError(_('No update container status file uploaded.'))

        # Read the uploaded Excel file
        file_content = base64.b64decode(self.upload_inventory_file)
        df = pd.read_excel(io.BytesIO(file_content))
        upload_file_columns = df.columns.tolist()

        # Compare headers
        if sample_file_columns != upload_file_columns:
            raise ValidationError(_('Invalid columns headers in the file uploaded'))

        return True
    
    def check_container_validations(self):
        """
        Container No. columns validations.
        :return:
        """
        if self.upload_inventory_file:
            file_content = base64.b64decode(self.upload_inventory_file)
            df = pd.read_excel(io.BytesIO(file_content))
             # Check for duplicate container numbers
            duplicate_containers = df['Container No.'].dropna()[df['Container No.'].dropna().duplicated()].tolist()

            if duplicate_containers:
                raise ValidationError(_('%s Duplicate container number found.', duplicate_containers))
            container_no_data = df['Container No.'].dropna().tolist()
            container_inventory = self.env['container.inventory'].search([]).mapped('name')
            get_active_container = self.env['container.inventory'].search([('location_id','=',self.location_id.id)]).mapped('name')
            if not get_active_container:
                raise ValidationError(_('There is no any active Container'))
            for rec in container_no_data:
                if rec not in container_inventory:
                    raise ValidationError(_('Container Number is not present in the Inventory'))
                elif not rec in get_active_container:
                    raise ValidationError(_('%s Container Number not found with Selected location',rec))
                
    def check_require_columns_data(self):
        """
        Validate that specified columns do not contain empty values.
        :return:
        """
        if self.upload_inventory_file:
            file_content = base64.b64decode(self.upload_inventory_file)
            df = pd.read_excel(io.BytesIO(file_content))
            require_columns = ['Container No.','Status To']
            for column in require_columns:
                if df[column].isnull().any() or df[column].eq('').any():
                    raise ValidationError(f"Column '{column}' should not contain empty values.")
            # Validate that specified columns do not contain empty or zero values.
    
    def get_data_sheet(self):
        """
        Get the data from the excel file
        :return:  list of data
        """
        data = []
        try:
            file_data = io.BytesIO(base64.b64decode(self.upload_inventory_file))
            wb = openpyxl.load_workbook(file_data)
            sheet = wb.active
            if sheet:
                data.append(sheet.max_row)
        except Exception as e:
            print(e)
        return data
    
    def check_status_validations(self):
        """
        Check status column validations.
        :return:
        """
        if not self.upload_inventory_file:
            raise ValidationError(_('No inventory file uploaded.'))
        file_content = base64.b64decode(self.upload_inventory_file)
        df = pd.read_excel(io.BytesIO(file_content))
        valid_status = {'AE', 'AA', 'AR', 'AV', 'DAV'}
        error_message = 'Please enter only "AE", "AA", "AR", "AV", or "DAV" as Status.\nFound invalid status: %s'
        # Get column data without NaN values
        column_data = df['Status To'].dropna()
        # Find invalid values
        invalid_values = column_data[~column_data.isin(valid_status)]
        if not invalid_values.empty:
            # Convert all invalid values to strings and join them
            invalid_value_index = invalid_values.index.tolist()
            result = [rec + 2 for rec in invalid_value_index]
            invalid_list = ', '.join(map(str, invalid_values.unique()))
            error_message = error_message + '\nInvalid rows: %s'
            raise ValidationError(
                _(error_message % (invalid_list, result))
            )

    @api.model
    def record_status_update_for_container_master(self):
        """
        Update Status records in container master if above all validation is passed.
        :return:
        """
        status_sequence = ['ae', 'aa', 'ar', 'av','dav']
        if self.upload_inventory_file:
            try:
                file_content = base64.b64decode(self.upload_inventory_file)
                df = pd.read_excel(io.BytesIO(file_content))
                df = df
                for index, row in df.iterrows():
                    container_no = self.env['container.inventory'].search([('location_id','=',self.location_id.id),('name', '=', row['Container No.'])],
                                                                           limit=1)
                    if container_no :
                        current_status = container_no.status
                        new_status = row['Status To'].lower()

                        if current_status and new_status:
                            if new_status == 'dav':
                                if current_status != 'ae':
                                    raise ValidationError("Status change to DAV can only be done for an AE container.")
                                else:
                                    vals = {'status': new_status}
                                    container_no.write(vals)
                            else:
                                current_index = status_sequence.index(current_status)
                                next_index = current_index + 1

                                if next_index < len(status_sequence) and status_sequence[next_index] == new_status:
                                    vals = {'status': new_status}
                                    container_no.write(vals)
                                else:
                                    raise ValidationError(f"Status change should be in the flow AE -> AA -> AR -> AV. Please choose the exact next status from the current status.")
            except Exception as e:
                raise ValidationError(_(e))
            return True
        return False
    
    def create_upload_container_status_record(self):
        """
        Create record in upload container status record while successfully passed all validations.
        :return:
        """
        try:
            vals = {
                'name': self.file_name,
                'uploaded_by': self.env.user.name,
                'rec_status': 'success',
                'upload_inventory_file': self.upload_inventory_file,
                'uploaded_on': datetime.now(),
            }
            new_record = self.env['update.container.status'].create(vals)
        except Exception as e:
            raise ValidationError(_('some issues while updating container Status data'))