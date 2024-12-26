import logging
from unittest.mock import patch
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class TestGstDetails(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env["res.partner"].create(
            {"name": "Test Partner", "l10n_in_pan": "COMP1234PA"}
        )

        cls.company = cls.env["res.company"].create(
            {"name": "Test Company", "pan": "COMP1234PA"}
        )

        cls.gst_cred = cls.env["gst.credentials"].create(
            {
                "email": "test_gst_cred@example.com",
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
            }
        )

    def test_default_get(self):
        """
        Test default_get to check if company_id is set correctly.
        """
        self.env.context = dict(self.env.context, active_id=self.company.id)
        defaults = self.env["gst.details"].default_get(["company_id"])
        self.assertEqual(
            defaults["company_id"],
            self.company.id,
            "Default company_id should be set correctly.",
        )

    @patch("requests.get")
    def test_get_gst_data(self, mock_get):
        """
        Test get_gst_data to ensure it handles valid responses and errors properly.
        """
        # Mock the requests.get to return a successful response
        mock_response = {
            "status_cd": "1",
            "data": {"gstin": "29COMP1234PAZ50", "status": "Active"},
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        gst_detail = self.env["gst.details"].create(
            {"gst_no": "29COMP1234PAZ50", "company_id": self.company.id}
        )

        response = gst_detail.get_gst_data(
            gst_no="29COMP1234PAZ50", company_id=self.company.id
        )
        self.assertEqual(
            response, mock_response, "The response data should match the mock response."
        )

        # Mock the requests.get to return an error response
        mock_response_error = {
            "status_cd": "0",
            "status_desc": "Invalid GSTIN",
            "error": {"error_cd": "GSTIN_NOT_FOUND", "message": "GSTIN not found"},
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response_error

        response = gst_detail.get_gst_data(
            gst_no="invalid_gst", company_id=self.company.id
        )
        self.assertIn(
            "error", response, "The response should contain an error message."
        )

    def test_validate_gst_number(self):
        """
        Test _validate_gst_number to ensure it correctly validates GST numbers.
        """
        gst_detail = self.env["gst.details"].create(
            {"gst_no": "29COMP1234PAZ50", "company_id": self.company.id}
        )
        # Test with valid GST number
        result = gst_detail._validate_gst_number("29COMP1234PAZ50", self.company.id)
        self.assertIn(
            "success",
            result,
            "The result should indicate success for a valid GST number.",
        )

        # Test with invalid GST number (length)
        result = gst_detail._validate_gst_number("123", self.company.id)
        self.assertIn(
            "error",
            result,
            "The result should indicate an error for an invalid GST number length.",
        )

        # Test with non-alphanumeric GST number
        result = gst_detail._validate_gst_number("29COMP!@#$%^&*", self.company.id)
        self.assertIn(
            "error",
            result,
            "The result should indicate an error for non-alphanumeric GST number.",
        )

        # Test with duplicate GST number
        with self.assertRaises(ValidationError) as e:
            self.env["gst.details"].create(
                {"gst_no": "29COMP1234PAZ50", "company_id": self.company.id}
            )
        self.assertEqual(
            e.exception.args[0],
            "29COMP1234PAZ50 is already added. Please enter another GST No.",
        )

        # Test with mismatched PAN
        result = gst_detail._validate_gst_number("29COMP1434PAZ50", self.company.id)
        self.assertIn(
            "error",
            result,
            "The result should indicate an error for a mismatched PAN.",
        )

    def test_check_gst_validations(self):
        """
        Test check_gst_validations to ensure it raises ValidationError for invalid GST numbers.
        """
        gst_detail = self.env["gst.details"].create(
            {"gst_no": "29COMP1234PAZ50", "company_id": self.company.id}
        )

        # Test with invalid GST number (length)
        with self.assertRaises(ValidationError) as e:
            gst_detail.gst_no = "123"
            gst_detail.check_gst_validations()
        self.assertEqual(
            e.exception.args[0],
            "GST Number entered should be 15 characters long. Please enter correct GST Number.",
        )

    def test_get_gst_credentials(self):
        """
        Test get_gst_credentials to ensure it returns credentials if they exist.
        """
        company = self.env["res.company"].create(
            {"name": "Test Company Modify Info", "pan": "ABCDE1234F"}
        )
        gst_detail = self.env["gst.details"].create(
            {"gst_no": "29ABCDE1234FZ50", "company_id": company.id}
        )

        email, client_id, client_secret = gst_detail.get_gst_credentials()
        self.assertIsNotNone(email)
        self.assertIsNotNone(client_id)
        self.assertIsNotNone(client_secret)

    def test_is_valid_gst_no(self):
        """
        Test is_valid_gst_no to ensure it raises ValidationError for invalid GST numbers.
        """
        company = self.env["res.company"].create(
            {"name": "Test Company Modify Info", "pan": "ABCDE1234F"}
        )

        gst_detail = self.env["gst.details"].create(
            {"gst_no": "29ABCDE1234FZ50", "company_id": company.id}
        )

        # Test with valid GST number
        gst_detail.is_valid_gst_no()

        # Test with invalid GST number (length)
        with self.assertRaises(ValidationError) as e:
            gst_detail.gst_no = "123"
        self.assertEqual(
            e.exception.args[0],
            "GST Number entered should be 15 characters long. Please enter correct GST Number.",
        )

        # Test with non-alphanumeric GST number

        with self.assertRaises(ValidationError) as e:
            gst_detail.gst_no = "29AB12365CDE!@#"
        self.assertEqual(e.exception.args[0], "Please Enter Alphanumeric Value")

    def test_check_gst_validations_parties_view(self):
        """
        Test check_gst_validations to ensure it updates partner details correctly in parties view context.
        """
        gst_detail = (
            self.env["gst.details"]
            .with_context(is_cms_parties_view=True)
            .create(
                {
                    "gst_no": "29COMP1234PAZ50",
                    "partner_id": self.partner.id,
                    "state": "Karnataka",
                    "legal_name": "Test Legal Name",
                    "gst_pincode": "560001",
                    "parties_add_line_1": "Test Address Line 1",
                    "parties_add_line_2": "Test Address Line 2",
                }
            )
        )

        gst_detail.check_gst_validations()

        self.assertEqual(
            self.partner.l10n_in_pan,
            "COMP1234PA",
            "The PAN should be updated for the partner.",
        )
        self.assertEqual(
            self.partner.gst_state,
            "Karnataka",
            "The GST state should be updated for the partner.",
        )
        self.assertEqual(
            self.partner.party_name,
            "Test Legal Name",
            "The legal name should be updated for the partner.",
        )
        self.assertEqual(
            self.partner.zip,
            "560001",
            "The pin code should be updated for the partner.",
        )
        self.assertEqual(
            self.partner.street,
            "Test Address Line 1",
            "The address line 1 should be updated for the partner.",
        )
        self.assertEqual(
            self.partner.street2,
            "Test Address Line 2",
            "The address line 2 should be updated for the partner.",
        )

    def test_get_create_record_info(self):
        """
        Test _get_create_record_info to ensure it correctly sets the creation record information.
        """
        self.env.user.tz = "UTC"
        # Create a company for this specific test
        company = self.env["res.company"].create(
            {"name": "Test Company Create Info", "pan": "CREATE1234"}
        )

        gst_detail = self.env["gst.details"].create(
            {"gst_no": "29CREATE1234FZ5", "company_id": company.id}
        )

        gst_detail._get_create_record_info()
        self.assertTrue(
            gst_detail.display_create_info, "The creation info should be set."
        )

    def test_get_modify_record_info(self):
        """
        Test _get_modify_record_info to ensure it correctly sets the modification record information.
        """
        # Create a company and user for this specific test
        self.env.user.tz = "UTC"
        company = self.env["res.company"].create(
            {"name": "Test Company Modify Info", "pan": "COMP1234PA"}
        )

        user = self.env["res.users"].create(
            {
                "name": "Test User Modify Info",
                "login": "test_user_modify_info",
                "email": "test_modify_info@example.com",
                "company_ids": [(4, company.id)],
                "company_id": company.id,
                "tz": "UTC",
            }
        )
        user.company_id = company.id
        user.write({"company_ids": [(4, company.id)]})

        gst_detail = self.env["gst.details"].create(
            {"gst_no": "29COMP1234PAZ50", "company_id": company.id}
        )

        with self.env.cr.savepoint():
            gst_detail.write({"tax_payer_type": "Updated Type"})
        gst_detail._get_modify_record_info()
        self.assertTrue(
            gst_detail.display_modified_info, "The modification info should be set."
        )

    def test_get_e_inv_applicable_values(self):
        """
        Test _get_e_inv_applicable_values to ensure it sets is_e_invoice_applicable correctly.
        """
        # Case 1: When not in parties view context and e-invoicing is applicable
        self.env.context = {}
        company = self.env["res.company"].create(
            {"name": "Test Company NEW", "e_invoice_applicable": "yes"}
        )
        gst_detail = self.env["gst.details"].create({"company_id": company.id})
        gst_detail._get_e_inv_applicable_values()
        self.assertTrue(
            gst_detail.is_e_invoice_applicable,
            "is_e_invoice_applicable should be True when e-invoicing is applicable.",
        )

    @patch("requests.get")
    def test_get_gst_data_for_parties(self, mock_get):
        """
        Test get_gst_data_for_parties to ensure it handles valid responses and errors properly.
        """
        # Mock the requests.get to return a successful response
        mock_response = {
            "status_cd": "1",
            "data": {"gstin": "29COMP1234PAZ50", "status": "Active"},
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        gst_detail = (
            self.env["gst.details"]
            .with_context(is_cms_parties_view=True, active_id=self.partner.id)
            .create({"gst_no": "29COMP1234PAZ50", "partner_id": self.partner.id})
        )

        response = gst_detail.get_gst_data_for_parties(
            gst_no="29COMP1234PAZ50", record_id=None
        )
        self.assertEqual(
            response,
            mock_response,
            "The response data should match the mock response for parties view.",
        )

        # Mock the requests.get to return an error response
        mock_response_error = {
            "status_cd": "0",
            "status_desc": "Invalid GSTIN",
            "error": {"error_cd": "GSTIN_NOT_FOUND", "message": "GSTIN not found"},
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response_error

        response = gst_detail.get_gst_data_for_parties(
            gst_no="invalid_gst", record_id=None
        )
        self.assertIn(
            "error",
            response,
            "The response should contain an error message for parties view.",
        )
