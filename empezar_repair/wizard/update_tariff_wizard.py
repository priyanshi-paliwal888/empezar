# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import io, os
import pandas as pd
import base64
from datetime import datetime

class UpdateTariffWizard(models.TransientModel):

    _name = "update.tariff.wizard"
    _description = "Update Tariff Wizard"

    file_name = fields.Char(string="File Name")
    shipping_line_id = fields.Many2one(
        "res.partner",
        string="Shipping Line",
        domain="[('is_shipping_line', '=', True)]", required=1
    )
    upload_tariff_file = fields.Binary(string="Upload File",
                                          help="Only XLS or XLSX files with max size of 5 MB and"
                                                                        " having max 200 entries.",
                                          required=True, copy=False, exportable=False)


    def check_validations_for_submit_data(self):
        """This method verify the uploaded wizard data.
        :return:
        """
        if self.upload_tariff_file:
            self.check_file_type_and_size_validations()
            file_content = base64.b64decode(self.upload_tariff_file)
            df = pd.read_excel(io.BytesIO(file_content))
            UpdateTariffWizard.check_header_files_validations(df)
            # UpdateTariffWizard.check_require_columns_data(df)
            self.create_in_progress_upload_tariff_record()
            active_records = self.env['update.tariff'].search([('rec_status', '=', 'in_progress')])
            for rec in active_records:
                rec.action_submit()
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        else:
            raise ValidationError(_('No Tariff file uploaded.'))

    def check_file_type_and_size_validations(self):
        """Check file type and file size validations.
        :return:
        """
        # Get the file name and check the extension
        file_name = self.file_name
        if not file_name.lower().endswith(('.xls', '.xlsx')):
            raise ValidationError(
                _("File Type selected is not allowed. Please upload files of types - .xls / .xlsx."))
        if len(self.upload_tariff_file) > 5242880:  # 5MB in bytes
            raise ValidationError(_("The maximum file size allowed should be 5 MB."))

    @staticmethod
    def check_header_files_validations(df):
        """compare sample file and uploaded file header if different then it will raise validation error.
        :return:
        """
        # Get the base path of the module
        module_base_path = os.path.dirname(os.path.dirname(__file__))

        # Construct the file path relative to the module's directory
        file_relative_path = 'static/src/document/Tariff Sample.xlsx'
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

    # @staticmethod
    # def check_require_columns_data(df):
    #     """Validate that specified columns do not contain empty values.
    #     :return:
    #     """
    #     require_columns = ['Damage location', 'Component', 'Damage Type', 'Repair Type', 'Measurement',
    #                        'Size/Type', 'Material Cost', 'Labour Hours', 'Key Value', 'Limit','Repair Code']
    #     for column in require_columns:
    #         if df[column].isnull().any() or df[column].eq('').any():
    #             raise ValidationError(f"Column '{column}' should not contain empty values.")

    def create_in_progress_upload_tariff_record(self):
        """Create in process records in upload inventory.
        :return:
        """
        try:
            vals = {
                'name': self.file_name,
                'uploaded_by': self.env.user.name,
                'uploaded_on': datetime.now(),
                'rec_status': 'in_progress',
                'upload_tariff_file': self.upload_tariff_file,
            }
            self.env['update.tariff'].create(vals)
        except Exception as e:
            raise ValidationError(_('Some issue while creating upload inventory records %s' % e))
