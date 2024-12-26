import logging
import io
import base64
from pandas import DataFrame
import pandas as pd
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


_logger = logging.getLogger(__name__)


class TestUploadContainerStatusWizard(TransactionCase):

    def setUp(self):
        super().setUp()

        self.location = self.env["res.company"].create(
            {
                "name": "Test Company",
            }
        )
        self.container1 = self.env["container.master"].create({"name": "FUJU1234568"})

        self.container2 = self.env["container.master"].create({"name": "EUJU1234567"})
        self.container1 = self.env["container.inventory"].create(
            {
                "name": "FUJU1234568",
                "location_id": self.location.id,
                "container_master_id": self.container1.id,
            }
        )

        self.container2 = self.env["container.inventory"].create(
            {
                "name": "EUJU1234567",
                "location_id": self.location.id,
                "container_master_id": self.container2.id,
            }
        )

    def test_action_submit(self):
        mock_data = pd.DataFrame(
            {
                "Container No.": ["GVTU3000389", "EUJU1234567"],
                "Status To": ["AE", "AA"],
                "Unnamed: 2": [False, False],
                "Please enter the abbreviations": [False, False],
                "Unnamed: 4": [False, False],
                "Note: Only 500 records can be uploaded at a time.": [False, False],
            }
        )

        df = DataFrame(mock_data)
        df["Container No."] = df["Container No."].astype(str)

        excel_file = io.BytesIO()
        df.to_excel(excel_file, index=False)
        excel_file.seek(0)
        base64_content = base64.b64encode(excel_file.read())

        wizard = self.env["update.container.wizard"].create(
            {
                "location_id": self.location.id,
                "file_name": "test.xls",
                "upload_inventory_file": base64_content,
            }
        )

        with self.assertRaises(ValidationError) as e:
            wizard.action_submit()
        self.assertEqual(
            e.exception.args[0],
            "GVTU3000389 Container Number not found with Selected location",
        )

    def test_check_header_files_validations_invalid_header(self):
        mock_data = pd.DataFrame(
            {
                "Container Number.": ["FUJU1234568", "EUJU1234567"],
                "Status To": ["AE", "AA"],
                "Unnamed: 2": [False, False],
                "Please enter the abbreviations": [False, False],
                "Unnamed: 4": [False, False],
            }
        )

        df = DataFrame(mock_data)
        excel_file = io.BytesIO()
        df.to_excel(excel_file, index=False)
        excel_file.seek(0)
        base64_content = base64.b64encode(excel_file.read())

        wizard = self.env["update.container.wizard"].create(
            {
                "location_id": self.location.id,
                "file_name": "test.xls",
                "upload_inventory_file": base64_content,
            }
        )
        with self.assertRaises(ValidationError) as e:
            wizard.check_header_files_validations()
        self.assertEqual(
            e.exception.args[0], "Invalid columns headers in the file uploaded"
        )

    def test_check_header_files_validations_no_file(self):
        wizard = self.env["update.container.wizard"].create(
            {
                "location_id": self.location.id,
                "file_name": "test.xls",
            }
        )
        with self.assertRaises(ValidationError) as e:
            wizard.check_header_files_validations()
        self.assertEqual(
            e.exception.args[0], "No update container status file uploaded."
        )

    def test_check_require_columns_data_without_container_column(self):
        mock_data = pd.DataFrame(
            {
                "Container No.": ["", ""],
                "Status To": ["AE", "AA"],
                "Unnamed: 2": [False, False],
                "Please enter the abbreviations": [False, False],
                "Unnamed: 4": [False, False],
                "Note: Only 500 records can be uploaded at a time.": [False, False],
            }
        )

        df = DataFrame(mock_data)
        excel_file = io.BytesIO()
        df.to_excel(excel_file, index=False)
        excel_file.seek(0)
        base64_content = base64.b64encode(excel_file.read())

        wizard = self.env["update.container.wizard"].create(
            {
                "location_id": self.location.id,
                "file_name": "test.xls",
                "upload_inventory_file": base64_content,
            }
        )

        with self.assertRaises(ValidationError) as e:
            wizard.check_require_columns_data()
        self.assertEqual(
            e.exception.args[0],
            "Column 'Container No.' should not contain empty values.",
        )

    def test_check_status_validations_invalid_status(self):
        mock_data = pd.DataFrame(
            {
                "Container No.": ["FUJU1234568", "EUJU1234567"],
                "Status To": ["CF", "KL"],
                "Unnamed: 2": [False, False],
                "Please enter the abbreviations": [False, False],
                "Unnamed: 4": [False, False],
                "Note: Only 500 records can be uploaded at a time.": [False, False],
            }
        )

        df = DataFrame(mock_data)
        excel_file = io.BytesIO()
        df.to_excel(excel_file, index=False)
        excel_file.seek(0)
        base64_content = base64.b64encode(excel_file.read())

        wizard = self.env["update.container.wizard"].create(
            {
                "location_id": self.location.id,
                "file_name": "test.xls",
                "upload_inventory_file": base64_content,
            }
        )

        with self.assertRaises(ValidationError) as e:
            wizard.check_status_validations()
        self.assertEqual(
            e.exception.args[0],
            'Please enter only "AE", "AA", "AR", "AV", or "DAV" as Status.\nFound invalid status: CF, KL\nInvalid rows: [2, 3]',
        )

    def test_record_status_update_for_container_master(self):
        mock_data = pd.DataFrame(
            {
                "Container No.": ["FUJU1234568", "EUJU1234567"],
                "Status To": ["AE", "AA"],
                "Unnamed: 2": [False, False],
                "Please enter the abbreviations": [False, False],
                "Unnamed: 4": [False, False],
                "Note: Only 500 records can be uploaded at a time.": [False, False],
            }
        )

        df = DataFrame(mock_data)
        df["Container No."] = df["Container No."].astype(str)

        excel_file = io.BytesIO()
        df.to_excel(excel_file, index=False)
        excel_file.seek(0)
        base64_content = base64.b64encode(excel_file.read())

        wizard = self.env["update.container.wizard"].create(
            {
                "location_id": self.location.id,
                "file_name": "test.xls",
                "upload_inventory_file": base64_content,
            }
        )
        wizard.record_status_update_for_container_master()

    def test_create_upload_container_status_record(self):
        mock_data = pd.DataFrame(
            {
                "Container No.": ["FUJU1234568", "EUJU1234567"],
                "Status To": ["AE", "AA"],
                "Unnamed: 2": [False, False],
                "Please enter the abbreviations": [False, False],
                "Unnamed: 4": [False, False],
                "Note: Only 500 records can be uploaded at a time.": [False, False],
            }
        )

        df = DataFrame(mock_data)
        df["Container No."] = df["Container No."].astype(str)

        excel_file = io.BytesIO()
        df.to_excel(excel_file, index=False)
        excel_file.seek(0)
        base64_content = base64.b64encode(excel_file.read())

        wizard = self.env["update.container.wizard"].create(
            {
                "location_id": self.location.id,
                "file_name": "test.xls",
                "upload_inventory_file": base64_content,
            }
        )
        wizard.create_upload_container_status_record()
