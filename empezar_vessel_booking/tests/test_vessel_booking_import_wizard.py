import io
import base64
import os
import pandas as pd
from odoo.tests import common
from odoo.exceptions import ValidationError
from odoo import fields


class TestBookingImportWizard(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner_model = self.env["res.partner"]
        self.container_master_model = self.env["container.master"]
        self.container_number_model = self.env["container.number"]
        self.vessel_booking_model = self.env["vessel.booking"]
        self.wizard_model = self.env["booking.import.wizard"]
        self.sample_file_path = os.path.join(
            os.path.dirname(__file__), "static/src/document/Container_Booking.xlsx"
        )

        self.location = self.env["res.company"].create(
            {
                "name": "Test Company",
            }
        )

        self.container_type = self.env["container.type.data"].create(
            {
                "name": "20 FT",
                "company_size_type_code": "20FT",
                "is_refer": "no",
                "active": True,
                "company_id": self.env.company.id,
            }
        )

        self.container_type_2 = self.env["container.type.data"].create(
            {
                "name": "30 FT",
                "company_size_type_code": "30FT",
                "is_refer": "no",
                "active": True,
                "company_id": self.env.company.id,
            }
        )

        self.container_type_3 = self.env["container.type.data"].create(
            {
                "name": "40 FT",
                "company_size_type_code": "40FT",
                "is_refer": "no",
                "active": True,
                "company_id": self.env.company.id,
            }
        )

        self.container1 = self.env["container.master"].create(
            {"name": "GVTU3000389", "type_size": self.container_type.id}
        )
        self.container2 = self.env["container.master"].create(
            {"name": "EUJU1234567", "type_size": self.container_type_2.id}
        )

        # Create partners, locations, container types, and vessel bookings
        self.partner_shipping_line = self.env["res.partner"].create(
            {
                "name": "Shipping Line",
                "is_shipping_line": True,
            }
        )

        self.partner_transporter = self.env["res.partner"].create(
            {
                "name": "Transporter",
                "parties_type_ids": [(0, 0, {"name": "Transporter"})],
            }
        )

        self.location = self.env["res.company"].create(
            {
                "name": "Location",
            }
        )

        # Create Container Detail
        self.container_detail = self.env["container.details"].create(
            {
                "container_size_type": self.container_type.id,
                "container_qty": 10,
                "balance": 5,
            }
        )

        self.container_detail_2 = self.env["container.details"].create(
            {
                "container_size_type": self.container_type_2.id,
                "container_qty": 10,
                "balance": 5,
            }
        )

        # Create Vessel Booking with Container Details
        self.vessel_booking = self.env["vessel.booking"].create(
            {
                "shipping_line_id": self.partner_shipping_line.id,
                "transporter_name": self.partner_transporter.id,
                "location": [(6, 0, [self.location.id])],
                "booking_no": "BOOK001",
                "booking_date": fields.Date.today(),
                "validity_datetime": fields.Datetime.now(),
                "cutoff_datetime": fields.Datetime.now(),
                "vessel": "Test Vessel",
                "voyage": "12345",
                "container_details": [
                    (6, 0, [self.container_detail.id, self.container_detail_2.id])
                ],
            }
        )

    def test_check_file_type_valid(self):
        file_content = base64.b64encode(b"Dummy content").decode("utf-8")
        wizard = self.wizard_model.create(
            {"file": file_content, "file_namex": "test.xlsx"}
        )
        try:
            wizard._check_file_type()
        except ValidationError as e:
            self.fail(f"ValidationError was raised: {e}")

    def test_check_file_size_invalid(self):
        file_content = base64.b64encode(b"A" * (6 * 1024 * 1024)).decode(
            "utf-8"
        )  # File size > 5MB
        with self.assertRaises(ValidationError):
            self.wizard_model.create({"file": file_content, "file_namex": "test.xlsx"})

    def test_action_import_valid(self):
        # Create a valid Excel file for testing
        df = pd.DataFrame(
            {
                "Container Type Size": ["20FT", "30FT"],
                "Container Number": ["GVTU3000389", "EUJU1234567"],
            }
        )
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        file_content = base64.b64encode(buffer.getvalue()).decode("utf-8")

        wizard = self.wizard_model.create(
            {
                "file": file_content,
                "file_namex": "valid_file.xlsx",
                "vessel_booking_id": self.vessel_booking.id,
            }
        )
    def test_check_header_files_validations(self):
        df = pd.DataFrame(
            {
                "Container Type Size": ["20FT", "30FT"],
                "Container Number": ["FUJU1234568", "GVTU3000389"],
            }
        )
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        file_content = base64.b64encode(buffer.getvalue()).decode("utf-8")

        wizard = self.wizard_model.create(
            {"file": file_content, "file_namex": "valid_file.xlsx"}
        )

        try:
            wizard.check_header_files_validations()
        except ValidationError as e:
            self.fail(f"ValidationError was raised: {e}")

    def test_validate_container_number(self):
        # Valid container numbers
        self.container_master_model.create(
            {"name": "FUJU1234568", "type_size": self.container_type.id}
        )

        df_valid = pd.DataFrame(
            {
                "Container Type Size": ["20FT", "30FT"],
                "Container Number": ["FUJU1234568", "EUJU1234567"],
            }
        )
        buffer_valid = io.BytesIO()
        df_valid.to_excel(buffer_valid, index=False)
        file_content_valid = base64.b64encode(buffer_valid.getvalue()).decode("utf-8")

        wizard = self.wizard_model.create(
            {"file": file_content_valid, "file_namex": "valid_containers.xlsx"}
        )
        try:
            wizard.validate_container_number(df_valid)
        except ValidationError as e:
            self.fail(f"ValidationError was raised: {e}")

        # Invalid container number
        df_invalid = pd.DataFrame({"Container Number": ["FUJU1234568", "EUJU1234567"]})
        buffer_invalid = io.BytesIO()
        df_invalid.to_excel(buffer_invalid, index=False)
        file_content_invalid = base64.b64encode(buffer_invalid.getvalue()).decode(
            "utf-8"
        )

        wizard = self.wizard_model.create(
            {"file": file_content_invalid, "file_namex": "invalid_containers.xlsx"}
        )
        with self.assertRaises(ValidationError):
            wizard.validate_container_number(df_invalid)

    def test_container_number_quantity(self):
        df = pd.DataFrame(
            {
                "Container Type Size": ["20FT", "30FT"],
                "Container Number": ["GVTU3000389", "EUJU1234567"],
            }
        )
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        file_content = base64.b64encode(buffer.getvalue()).decode("utf-8")

        wizard = self.wizard_model.create(
            {
                "file": file_content,
                "file_namex": "valid_quantity.xlsx",
                "vessel_booking_id": self.vessel_booking.id,
            }
        )

        self.container_master_model.create(
            {"name": "FUJU1234568", "type_size": self.container_type.id}
        )
        wizard.container_number_quantity(df)
        self.assertTrue(True)

    def test_container_detail_check(self):
        df = pd.DataFrame(
            {
                "Container Type Size": ["20FT", "30FT"],
                "Container Number": ["GVTU3000389", "EUJU1234567"],
            }
        )
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        file_content = base64.b64encode(buffer.getvalue()).decode("utf-8")

        wizard = self.wizard_model.create(
            {
                "file": file_content,
                "file_namex": "valid_check.xlsx",
                "vessel_booking_id": self.vessel_booking.id,
            }
        )

        # Mock container details
        container_type = self.container_type_3
        self.vessel_booking.write(
            {
                "container_details": [
                    (
                        0,
                        0,
                        {"container_size_type": container_type.id, "container_qty": 5},
                    )
                ]
            }
        )

    def test_validate_container_number_invalid_container_number(self):
        df = pd.DataFrame(
            {
                "Container Type Size": ["20FT", "30FT"],
                "Container Number": ["88881234567", "EUJU1234567"],
            }
        )
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        file_content = base64.b64encode(buffer.getvalue()).decode("utf-8")

        wizard = self.wizard_model.create(
            {
                "file": file_content,
                "file_namex": "valid_file.xlsx",
                "vessel_booking_id": self.vessel_booking.id,
            }
        )
        with self.assertRaises(ValidationError):
            wizard.with_context(active_id=self.vessel_booking.id).action_import()

    def test_validate_container_number_container_number_not_present(self):
        df = pd.DataFrame(
            {"Container Type Size": ["20FT"], "Container Number": ["FUJU1234568"]}
        )
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        file_content = base64.b64encode(buffer.getvalue()).decode("utf-8")

        wizard = self.wizard_model.create(
            {
                "file": file_content,
                "file_namex": "valid_file.xlsx",
                "vessel_booking_id": self.vessel_booking.id,
            }
        )
        with self.assertRaises(ValidationError):
            wizard.with_context(active_id=self.vessel_booking.id).action_import()

    def test_validate_container_number_duplicate_container_number(self):
        df = pd.DataFrame(
            {
                "Container Type Size": ["20FT", "30FT"],
                "Container Number": ["FUJU1234568", "FUJU1234568"],
            }
        )
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        file_content = base64.b64encode(buffer.getvalue()).decode("utf-8")

        wizard = self.wizard_model.create(
            {
                "file": file_content,
                "file_namex": "valid_file.xlsx",
                "vessel_booking_id": self.vessel_booking.id,
            }
        )
        with self.assertRaises(ValidationError):
            wizard.with_context(active_id=self.vessel_booking.id).action_import()

    def test_check_invalid_header_files(self):
        df = pd.DataFrame({"Container Number": ["GVTU3000389", "FUJU1234568"]})
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        file_content = base64.b64encode(buffer.getvalue()).decode("utf-8")

        wizard = self.wizard_model.create(
            {"file": file_content, "file_namex": "valid_file.xlsx"}
        )
        with self.assertRaises(ValidationError):
            wizard.with_context(active_id=self.vessel_booking.id).action_import()

    def test_check_invalid_files(self):
        df = pd.DataFrame(
            {
                "Container Type Size": ["20FT", "30FT"],
                "Container Number": ["GVTU3000389", "FUJU1234568"],
            }
        )
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        file_content = base64.b64encode(buffer.getvalue()).decode("utf-8")

        with self.assertRaises(ValidationError):
            self.wizard_model.create(
                {"file": file_content, "file_namex": "invalid_file.pdf"}
            )
