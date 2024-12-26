from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
from odoo import fields


class TestContainerDetailsMoveout(TransactionCase):

    def setUp(self):
        super().setUp()

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

        self.container_type = self.env["container.type.data"].create(
            {
                "name": "20 FT",
                "company_size_type_code": "20FT",
                "is_refer": "no",
                "active": True,
                "company_id": self.env.company.id,
            }
        )

        self.container_details = self.env["container.details"].create(
            {
                "container_size_type": self.container_type.id,
                "container_qty": 10,
                "balance": 5,
            }
        )
        self.booking = self.env["vessel.booking"].create(
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
                "container_details": [(6, 0, [self.container_details.id])],
            }
        )

    def test_balance_computation(self):
        """ Test balance computation for containers. """
        # Get the initial balance
        initial_balance = self.container_details.balance

        # Ensure the balance is computed correctly
        self.container_details._compute_balance()
        self.assertEqual(self.container_details.balance, initial_balance)

    def test_container_qty_validity(self):
        """ Test validation for container quantity. """
        # Test valid container quantity
        self.container_details.container_qty = 10  # This should be valid
        self.container_details._check_container_qty()  # Should not raise

        # Test invalid container quantity (less than 1)
        with self.assertRaises(ValidationError):
            self.container_details.container_qty = 0
            self.container_details._check_container_qty()

        # Test invalid container quantity (greater than 999)
        with self.assertRaises(ValidationError):
            self.container_details.container_qty = 1000
            self.container_details._check_container_qty()

    def test_container_qty_constraint_with_move_in_out(self):
        """ Test the constraint when container sizes are used in Move In or Move Out. """
        # Set up the scenario where container size is used in Move In or Move Out
        self.container_details.container_qty = 1  # Set it to a lower number

        with self.assertRaises(ValidationError):
            self.container_details._check_container_qty()  # Should raise because qty < expected

        # Update the container master to simulate container being used
        self.move_in_record.container = 'CONTAINER1'  # Now used in Move In
        self.container_details.container_qty = 2  # Set to a higher number
        self.container_details._check_container_qty()