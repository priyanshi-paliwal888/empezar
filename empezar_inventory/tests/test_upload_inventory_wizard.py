import base64
import io
import pandas as pd
from pandas import DataFrame

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestUploadInventoryWizard(TransactionCase):

    def setUp(self):
        super().setUp()
        self.wizard_obj = self.env["upload.inventory.wizard"]
        self.company = self.env.ref("base.main_company")
        self.user = self.env.user

    def test_check_validations_for_submit_data(self):

        mock_data = pd.DataFrame(
            {
                "Sr. No. ": [False, False],
                "Shipping Line": [False, False],
                "Container No.": ["12365478921", "12365478922"],
                "Size/Type": ["Size/Type A", "Size/Type B"],
                "In Date": ["12/01/2023", "10/01/2023"],
                "In Time": ["08:00:00", "10:00:00"],
                "Status": ["AE", "AA"],
                "Production Month/Year": ["05/2024", "07/2024"],
                "Grade": ["A", "B"],
                "Damage Condition": ["Damage A", "Damage B"],
                "Gross Wt.": [25, 30],
                "Tare Wt.": [26, 31],
                "Estimate Date": ["20/01/2023", "12/01/2023"],
                "Estimate Amt": [1000.0, 2000.0],
                "Approval Date": ["25/01/2023", "14/01/2023"],
                "Approved Amount": [800.0, 1800.0],
                "Repair Date": ["26/01/2023", "16/01/2023"],
                "Remarks": ["Test remark 1", "Test remark 2"],
                "Unnamed: 18": [False, False],
                "Note: Only 200 records can be uploaded at a time.": [False, False],
            }
        )

        df = DataFrame(mock_data)
        excel_file = io.BytesIO()
        df.to_excel(excel_file, index=False)
        excel_file.seek(0)
        base64_content = base64.b64encode(excel_file.read())

        wizard = self.wizard_obj.create(
            {
                "file_name": "test_file.xlsx",
                "location_id": self.company.id,
                "upload_inventory_file": base64_content,
            }
        )
        wizard.check_validations_for_submit_data()

    def test_check_header_files_validations_invalid_header(self):
        mock_data = pd.DataFrame(
            {
                "Sr. Number. ": [False, False],  # Invalid Header
                "Shipping Line": [False, False],
                "Container No.": ["12365478921", "12365478922"],
                "Size/Type": ["Size/Type A", "Size/Type B"],
                "In Date": ["12/01/2023", "10/01/2023"],
                "In Time": ["08:00:00", "10:00:00"],
                "Status": ["AE", "AA"],
                "Production Month/Year": ["05/2024", "07/2024"],
                "Grade": ["A", "B"],
                "Damage Condition": ["Damage A", "Damage B"],
                "Gross Wt.": [25, 30],
                "Tare Wt.": [26, 31],
                "Estimate Date": ["20/01/2023", "12/01/2023"],
                "Estimate Amt": [1000.0, 2000.0],
                "Approval Date": ["25/01/2023", "14/01/2023"],
                "Approved Amount": [800.0, 1800.0],
                "Repair Date": ["26/01/2023", "16/01/2023"],
                "Remarks": ["Test remark 1", "Test remark 2"],
                "Unnamed: 18": [False, False],
                "Note: Only 200 records can be uploaded at a time.": [False, False],
            }
        )
        df = DataFrame(mock_data)
        excel_file = io.BytesIO()
        df.to_excel(excel_file, index=False)
        excel_file.seek(0)
        base64_content = base64.b64encode(excel_file.read())

        wizard = self.wizard_obj.create(
            {
                "file_name": "test_file.xlsx",
                "location_id": self.company.id,
                "upload_inventory_file": base64_content,
            }
        )
        with self.assertRaises(ValidationError) as e:
            wizard.check_validations_for_submit_data()
        self.assertEqual(
            e.exception.args[0], "Invalid columns headers in the file uploaded"
        )

    def test_check_require_columns_data_invalid_value(self):
        mock_data = pd.DataFrame(
            {
                "Sr. No. ": [False, False],
                "Shipping Line": [False, False],
                "Container No.": ["12365478921", "12365478922"],
                "Size/Type": ["Size/Type A", "Size/Type B"],
                "In Date": ["12/01/2023", "10/01/2023"],
                "In Time": ["08:00:00", "10:00:00"],
                "Status": ["AE", "AA"],
                "Production Month/Year": ["05/2024", "07/2024"],
                "Grade": ["A", "B"],
                "Damage Condition": ["Damage A", "Damage B"],
                "Gross Wt.": [25, 30],
                "Tare Wt.": ["", 31],  # Invalid Values Pass
                "Estimate Date": ["20/01/2023", "12/01/2023"],
                "Estimate Amt": [1000.0, 2000.0],
                "Approval Date": ["25/01/2023", "14/01/2023"],
                "Approved Amount": [800.0, 1800.0],
                "Repair Date": ["26/01/2023", "16/01/2023"],
                "Remarks": ["Test remark 1", "Test remark 2"],
                "Unnamed: 18": [False, False],
                "Note: Only 200 records can be uploaded at a time.": [False, False],
            }
        )
        df = DataFrame(mock_data)
        excel_file = io.BytesIO()
        df.to_excel(excel_file, index=False)
        excel_file.seek(0)
        base64_content = base64.b64encode(excel_file.read())

        wizard = self.wizard_obj.create(
            {
                "file_name": "test_file.xlsx",
                "location_id": self.company.id,
                "upload_inventory_file": base64_content,
            }
        )

        with self.assertRaises(ValidationError) as e:
            wizard.check_validations_for_submit_data()
        self.assertEqual(
            e.exception.args[0],
            "Column 'Tare Wt.' should not contain empty or zero values.",
        )

    def test_check_require_columns_data_zero_value(self):
        mock_data = pd.DataFrame(
            {
                "Sr. No. ": [False, False],  # Invalid Header
                "Shipping Line": [False, False],
                "Container No.": ["12365478921", "12365478922"],
                "Size/Type": ["Size/Type A", "Size/Type B"],
                "In Date": ["12/01/2023", "10/01/2023"],
                "In Time": ["08:00:00", "10:00:00"],
                "Status": ["AE", "AA"],
                "Production Month/Year": ["05/2024", "07/2024"],
                "Grade": ["A", "B"],
                "Damage Condition": ["Damage A", "Damage B"],
                "Gross Wt.": [25, 30],
                "Tare Wt.": [0, 31],  # Invalid Values Pass
                "Estimate Date": ["20/01/2023", "12/01/2023"],
                "Estimate Amt": [1000.0, 2000.0],
                "Approval Date": ["25/01/2023", "14/01/2023"],
                "Approved Amount": [800.0, 1800.0],
                "Repair Date": ["26/01/2023", "16/01/2023"],
                "Remarks": ["Test remark 1", "Test remark 2"],
                "Unnamed: 18": [False, False],
                "Note: Only 200 records can be uploaded at a time.": [False, False],
            }
        )
        df = DataFrame(mock_data)
        excel_file = io.BytesIO()
        df.to_excel(excel_file, index=False)
        excel_file.seek(0)
        base64_content = base64.b64encode(excel_file.read())

        wizard = self.wizard_obj.create(
            {
                "file_name": "test_file.xlsx",
                "location_id": self.company.id,
                "upload_inventory_file": base64_content,
            }
        )

        with self.assertRaises(ValidationError) as e:
            wizard.check_validations_for_submit_data()
        self.assertEqual(
            e.exception.args[0],
            "Column 'Tare Wt.' should not contain empty or zero values.",
        )
