import logging
import io
import base64
import pandas as pd
from pandas import DataFrame
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

        self.hold_reason = self.env["hold.reason"].create(
            {
                "company_id": self.location.id,
                "name": "hold reason 1",
            }
        )

    def test_check_container_validations_duplicate_number(self):
        mock_data = pd.DataFrame(
            {
                "Container No.": ["12365478921", "12365478921"],
                "Unnamed: 1": [False, False],
                "Note: Only 200 records can be uplaoded at a time.": [False, False],
            }
        )

        df = DataFrame(mock_data)
        df["Container No."] = df["Container No."].astype(str)

        excel_file = io.BytesIO()
        df.to_excel(excel_file, index=False)
        excel_file.seek(0)
        base64_content = base64.b64encode(excel_file.read())

        wizard = self.env["hold.release.container.wizard"].create(
            {
                "location_id": self.location.id,
                "file_name": "test.xls",
                "upload_file": base64_content,
                "hold_reason_id": self.hold_reason.id,
                "remarks": "Testing",
            }
        )

        with self.assertRaises(ValidationError) as e:
            wizard.check_container_validations()
        self.assertEqual(
            e.exception.args[0], "[12365478921] Duplicate container number found."
        )
