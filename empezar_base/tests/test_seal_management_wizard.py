from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestSealManagementWizard(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Shipping Line",
                "is_shipping_line": True,
            }
        )
        self.company = self.env["res.company"].create(
            {
                "name": "Test Company",
                "parent_id": False,
            }
        )

    def test_action_create_valid_data(self):
        wizard_data = {
            "location": self.company.id,
            "shipping_line_id": self.partner.id,
            "prefix": "TEST",
            "start_range": 1,
            "end_range": 5,
        }
        wizard = self.env["seal.management.wizard"].create(wizard_data)
        wizard.action_create()

        # Check if seal records were created
        seal_records = self.env["seal.management"].search(
            [
                ("location", "=", self.company.id),
                ("shipping_line_id", "=", self.partner.id),
                ("seal_number", "in", ["TEST1", "TEST2", "TEST3", "TEST4", "TEST5"]),
            ]
        )
        self.assertEqual(len(seal_records), 5, "Expected 5 seal records to be created")

    def test_check_ranges_constraint(self):
        wizard_data = {
            "location": self.company.id,
            "shipping_line_id": self.partner.id,
            "prefix": "TEST",
            "start_range": 0,
            "end_range": -5,
        }
        with self.assertRaises(ValidationError) as e:
            self.env["seal.management.wizard"].create(wizard_data)
        self.assertEqual(
            e.exception.args[0], "Please add any positive numbers in range."
        )

        wizard_data["start_range"] = 10
        wizard_data["end_range"] = 1
        with self.assertRaises(ValidationError) as e:
            self.env["seal.management.wizard"].create(wizard_data)
        self.assertEqual(
            e.exception.args[0],
            "End Range value cannot be less than the Start Range value.",
        )

        wizard_data["end_range"] = 1020
        with self.assertRaises(ValidationError) as e:
            self.env["seal.management.wizard"].create(wizard_data)
        self.assertEqual(
            e.exception.args[0],
            "The number of seal records to be created should not be more than 1000.",
        )

    def test_handle_duplicate_seal_numbers(self):
        # Create initial seal record
        seal_record = self.env["seal.management"].create(
            {
                "seal_number": "DUPLICATE001",
                "location": self.company.id,
                "shipping_line_id": self.partner.id,
            }
        )

        # Mock the send_seal_failure_email method to track calls
        original_send_email = self.env[
            "seal.management.wizard"
        ].send_seal_failure_email(self.env.context)
        # self.env['seal.management.wizard'].send_seal_failure_email(lambda ctx: self.assertIn('failure_reason', ctx, "Expected failure reason in context"))

        # Create the wizard and call handle_duplicate_seal_numbers with a duplicate seal number
        wizard = self.env["seal.management.wizard"].create(
            {
                "location": self.company.id,
                "shipping_line_id": self.partner.id,
                "prefix": "DUPLICATE",
                "start_range": 1,
                "end_range": 1,
            }
        )
        with self.assertRaises(ValidationError) as e:
            wizard.handle_duplicate_seal_numbers(["DUPLICATE001"])
        self.assertEqual(e.exception.args[0], "Seal Number already present.")

    def test_action_create_prefix_validation(self):
        wizard_data = {
            "location": self.company.id,
            "shipping_line_id": self.partner.id,
            "prefix": "TEST!",
            "start_range": "1",
            "end_range": "5",
        }

        with self.assertRaises(ValidationError) as e:
            wizard = self.env["seal.management.wizard"].create(wizard_data)
            wizard.action_create()

        self.assertEqual(
            e.exception.args[0], "Please Enter Alphanumeric Value in Prefix."
        )
