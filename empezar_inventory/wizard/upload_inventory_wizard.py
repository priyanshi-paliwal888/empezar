# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import openpyxl
import io, os
import base64
import pandas as pd
from datetime import datetime


class UploadInventoryWizard(models.TransientModel):

    _name = "upload.inventory.wizard"
    _description = "Upload Inventory Wizard"

    file_name = fields.Char(string="File Name")
    location_id = fields.Many2one('res.company', string="Location", required=True, domain="[('parent_id','!=',False)]")
    upload_inventory_file = fields.Binary(string="Upload File",
                                          help="Only XLS or XLSX files with max size of 5 MB and"
                                                                        " having max 200 entries.",
                                          required=True, copy=False, exportable=False)

    def check_validations_for_submit_data(self):
        """
        This method verify the uploaded wizard data.
        :return:
        """
        if self.upload_inventory_file:
            self.check_file_type_and_size_validations()
            # Read the uploaded Excel file
            file_content = base64.b64decode(self.upload_inventory_file)
            df = pd.read_excel(io.BytesIO(file_content))
            UploadInventoryWizard.check_header_files_validations(df)
            UploadInventoryWizard.check_require_columns_data(df)
            self.check_data_length_validations()
            self.create_in_progress_upload_inventory_record()
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        else:
            raise ValidationError(_('No inventory file uploaded.'))

    def create_in_progress_upload_inventory_record(self):
        """
        Create in process records in upload inventory.
        :return:
        """
        try:
            vals = {
                'name': self.file_name,
                'uploaded_by': self.env.user.name,
                'uploaded_on': datetime.now(),
                'rec_status': 'in_progress',
                'upload_inventory_file': self.upload_inventory_file,
                'location_id': self.location_id.id
            }
            new_record = self.env['upload.inventory'].create(vals)
        except Exception as e:
            raise ValidationError(_('Some issue while creating upload inventory records %s' % e))

    @staticmethod
    def check_header_files_validations(df):
        """
        compare sample file and uploaded file header if different then it will raise validation error.
        :return:
        """
        # Get the base path of the module
        module_base_path = os.path.dirname(os.path.dirname(__file__))

        # Construct the file path relative to the module's directory
        file_relative_path = 'static/src/document/Upload_Inventory_Sample.xlsx'
        sample_file_path = os.path.join(module_base_path, file_relative_path)

        # Check if the sample file exists
        if not os.path.exists(sample_file_path):
            raise ValidationError(_('The specified sample Excel file does not exist.'))

        # Read the sample Excel file to get its columns
        sample_df = pd.read_excel(sample_file_path)
        sample_file_columns = sample_df.columns.tolist()

        upload_file_columns = df.columns.tolist()

        # Compare headers
        if sample_file_columns != upload_file_columns:
            raise ValidationError(_('Invalid columns headers in the file uploaded'))

        return True

    @staticmethod
    def check_require_columns_data(df):
        """
        Validate that specified columns do not contain empty values.
        :return:
        """
        require_columns = ['Shipping Line', 'Container No.', 'Size/Type', 'Production Month/Year',
                           'Damage Condition']
        for column in require_columns:
            if df[column].isnull().any() or df[column].eq('').any():
                raise ValidationError(f"Column '{column}' should not contain empty values.")
        # Validate that specified columns do not contain empty or zero values.
        weight_columns = ['Tare Wt.', 'Gross Wt.']
        for column in weight_columns:
            if df[column].isnull().any() or (df[column] == 0).any() or df[column].eq('').any():
                raise ValidationError(f"Column '{column}' should not contain empty or zero values.")

    def check_file_type_and_size_validations(self):
        """
        Check file type and file size validations.
        :return:
        """
        # Get the file name and check the extension
        file_name = self.file_name
        if not file_name.lower().endswith(('.xls', '.xlsx')):
            raise ValidationError(
                _("File Type selected is not allowed. Please upload files of types - .xls / .xlsx."))
        if len(self.upload_inventory_file) > 5242880:  # 5MB in bytes
            raise ValidationError("The maximum file size allowed should be 5 MB.")

    def check_data_length_validations(self):
        """
        Verify the row size of uploaded Excel file.
        :return:
        """
        data = self.get_data_sheet()
        if data and data[0] > 10001:
            raise ValidationError(_('Records entered are more than 10000. Kindly'
                                    ' re-upload with 10000 or fewer records.'))

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
