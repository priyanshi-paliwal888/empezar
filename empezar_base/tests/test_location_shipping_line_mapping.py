# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from odoo.addons.empezar_base.models.contrainer_type_edi import ContainerTypeEdi


class TestLocationShippingLineMapping(TransactionCase):

    def setUp(self):
        super().setUp()
        # Create a test company
        self.company = self.env["res.company"].create(
            {
                "name": "Test Company",
            }
        )

        # Create a test shipping line
        self.shipping_line = self.env["res.partner"].create(
            {
                "name": "Test Shipping Line",
                "company_id": self.company.id,
            }
        )

        # Create another shipping line for testing constraints
        self.another_shipping_line = self.env["res.partner"].create(
            {
                "name": "Another Shipping Line",
                "company_id": self.company.id,
            }
        )

        # Create a test user
        self.user = self.env["res.users"].create(
            {
                "name": "Test User",
                "login": "test_user",
                "company_ids": [(4, self.company.id)],
                "company_id": self.company.id,
                "tz": "UTC",
            }
        )

    def test_create_record_info(self):
        """
        Test _get_create_record_info to ensure it correctly sets the creation record information.
        """
        self.env.user.tz = "UTC"
        mapping = (
            self.env["location.shipping.line.mapping"]
            .with_user(self.user)
            .create(
                {
                    "company_id": self.company.id,
                    "shipping_line_id": self.shipping_line.id,
                }
            )
        )
        mapping._get_create_record_info()
        self.assertTrue(mapping.display_create_info, "The creation info should be set.")

    def test_modify_record_info(self):
        """
        Test _get_modify_record_info to ensure it correctly sets the modification record information.
        """
        self.env.user.tz = "UTC"
        mapping = self.env["location.shipping.line.mapping"].create(
            {
                "company_id": self.company.id,
                "shipping_line_id": self.shipping_line.id,
            }
        )
        # Change a field to trigger the modification info update
        mapping.with_user(self.user).write(
            {
                "gate_pass": "move_in",
            }
        )
        mapping._get_modify_record_info()
        self.assertTrue(
            mapping.display_modified_info, "The modification info should be set."
        )

    def test_email_validation(self):
        """
        Test email validation logic.
        """
        with self.assertRaises(
            ValidationError,
            msg="Invalid email address. Please enter a correct email address.",
        ):
            mapping = self.env["location.shipping.line.mapping"].create(
                {
                    "company_id": self.company.id,
                    "shipping_line_id": self.shipping_line.id,
                    "from_email": "invalidemail",
                    "to_email": "test@valid.com",
                    "cc_email": "test@valid.com",
                }
            )

        with self.assertRaises(
            ValidationError,
            msg="Invalid email address. Please enter a correct email address.",
        ):
            mapping = self.env["location.shipping.line.mapping"].create(
                {
                    "company_id": self.company.id,
                    "shipping_line_id": self.shipping_line.id,
                    "from_email": "test@valid.com",
                    "to_email": "invalidemail",
                    "cc_email": "test@valid.com",
                }
            )

        with self.assertRaises(
            ValidationError,
            msg="Invalid email address. Please enter a correct email address.",
        ):
            mapping = self.env["location.shipping.line.mapping"].create(
                {
                    "company_id": self.company.id,
                    "shipping_line_id": self.shipping_line.id,
                    "from_email": "test@valid.com",
                    "to_email": "test@valid.com",
                    "cc_email": "invalidemail",
                }
            )

    def test_shipping_line_constraint(self):
        """
        Test check_shipping_line_validation to ensure duplicate shipping lines are not allowed for the same company.
        """
        mapping = self.env["location.shipping.line.mapping"].create(
            {
                "company_id": self.company.id,
                "shipping_line_id": self.shipping_line.id,
            }
        )
        with self.assertRaises(ValidationError, msg="Shipping Line is already mapped"):
            self.env["location.shipping.line.mapping"].create(
                {
                    "company_id": self.company.id,
                    "shipping_line_id": self.shipping_line.id,
                }
            )

        # Test allowing a different shipping line for the same company
        mapping_2 = self.env["location.shipping.line.mapping"].create(
            {
                "company_id": self.company.id,
                "shipping_line_id": self.another_shipping_line.id,
            }
        )
        self.assertTrue(
            mapping_2,
            "A different shipping line should be allowed for the same company.",
        )

    def test_active_status_computation(self):
        """
        Test _check_active_records to ensure it computes the correct active status.
        """
        mapping = self.env["location.shipping.line.mapping"].create(
            {
                "company_id": self.company.id,
                "shipping_line_id": self.shipping_line.id,
                "active": True,
            }
        )
        ContainerTypeEdi.check_active_records(mapping)
        self.assertEqual(
            mapping.rec_status,
            "active",
            "The record should be active when active is True.",
        )

        mapping.active = False
        ContainerTypeEdi.check_active_records(mapping)
        self.assertEqual(
            mapping.rec_status,
            "disable",
            "The record should be disabled when active is False.",
        )

    def test_get_gate_pass_values(self):
        """
        Test _get_gate_pass_values to ensure it correctly sets the gate pass values.
        """
        # Create a mapping record with gate pass options
        mapping = self.env["location.shipping.line.mapping"].create(
            {
                "company_id": self.company.id,
                "shipping_line_id": self.shipping_line.id,
                "gate_pass_ids": [
                    (
                        6,
                        0,
                        [
                            self.env.ref("empezar_base.gate_pass_move_in").id,
                            self.env.ref("empezar_base.gate_pass_move_out").id,
                        ],
                    )
                ],
            }
        )

        # Trigger computation
        mapping._get_gate_pass_values()

        # Check if the gate pass field is correctly set
        self.assertEqual(
            mapping.gate_pass,
            "Move In, Move Out",
            "Gate pass values should be 'Move In, Move Out'.",
        )

    def test_labour_rate_numeric_validation(self):
        """
        Test _labour_rate_numeric_validation to ensure it correctly validates numeric Labour Rate.
        """
        # Create a mapping record with a non-numeric Labour Rate
        with self.assertRaises(
            ValidationError, msg="The Labour Rate must contain only numeric values."
        ):
            mapping = self.env["location.shipping.line.mapping"].create(
                {
                    "company_id": self.company.id,
                    "shipping_line_id": self.shipping_line.id,
                    "labour_rate": "ABC",  # Non-numeric value
                }
            )

    def test_capacity_numeric_validation(self):
        """
        Test _capacity_numeric_validation to ensure it correctly validates numeric Capacity.
        """
        # Create a mapping record with a non-numeric Capacity
        with self.assertRaises(
            ValidationError, msg="The Capacity must contain only numeric values."
        ):
            mapping = self.env["location.shipping.line.mapping"].create(
                {
                    "company_id": self.company.id,
                    "shipping_line_id": self.shipping_line.id,
                    "capacity": "XYZ",  # Non-numeric value
                }
            )
