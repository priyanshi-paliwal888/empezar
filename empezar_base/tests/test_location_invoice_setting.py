# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestLocationInvoiceSetting(TransactionCase):

    def setUp(self):
        super().setUp()
        # Create a test company
        self.company = self.env["res.company"].create(
            {
                "name": "Test Company",
                "street": "123 Main St",
                "street2": "Suite 456",
                "city": "Test City",
                "zip": "12345",
                "country_id": self.env.ref(
                    "base.us"
                ).id,  # Assuming 'base.us' is a valid country in your data
                "state_id": self.env.ref(
                    "base.state_us_1"
                ).id,  # Assuming 'base.state_us_1' is a valid state in your data
                "cin": "L12345MH2024PTC567890",
            }
        )

        # Create a test shipping line
        self.shipping_line = self.env["res.partner"].create(
            {
                "name": "Test Shipping Line",
                "company_id": self.company.id,
            }
        )

        self.lift_on_option = self.env.ref("empezar_base.inv_applicable_lift_on")
        self.lift_off_option = self.env.ref("empezar_base.inv_applicable_lift_off")
        self.others_option = self.env.ref("empezar_base.inv_applicable_others")

        self.payment_mode_cash = self.env.ref("empezar_base.payment_mode_cash")
        self.payment_mode_online = self.env.ref("empezar_base.payment_mode_online")

    def test_default_get(self):
        """
        Test default_get method to ensure payment_mode_ids is set correctly.
        """
        context = {}
        default_get_model = self.env["location.invoice.setting"].with_context(context)

        fields_list = ["payment_mode_ids"]
        defaults = default_get_model.default_get(fields_list)
        self.assertIn(
            "payment_mode_ids", defaults, "payment_mode_ids should be in defaults."
        )

        payment_mode_cash_id = self.env.ref("empezar_base.payment_mode_cash").id
        if payment_mode_cash_id:
            self.assertEqual(
                defaults["payment_mode_ids"],
                [payment_mode_cash_id],
                "Default payment_mode_ids should contain payment_mode_cash_id.",
            )
        else:
            self.assertEqual(
                defaults["payment_mode_ids"],
                [],
                "Default payment_mode_ids should be empty when payment_mode_cash_id does not exist.",
            )

    def test_onchange_gst_no(self):
        """
        Test onchange_gst_no to check the GST No field updates.
        """
        location_inv_setting = self.env["location.invoice.setting"].create(
            {"company_id": self.company.id, "gst_no": "same_as_cmp"}
        )
        main_company = self.env["res.company"].search(
            [("parent_id", "=", False)], limit=1
        )
        location_inv_setting.onchange_gst_no()
        self.assertEqual(
            location_inv_setting.cin_no,
            main_company.cin,
            "CIN should be set to company's CIN when GST No is same as company.",
        )

        # Change GST No to others and check if CIN is cleared
        location_inv_setting.gst_no = "others"
        location_inv_setting.onchange_gst_no()
        self.assertFalse(
            location_inv_setting.cin_no,
            "CIN should be cleared when GST No is set to others.",
        )

    #
    def test_check_shipping_line_validation(self):
        """
        Test check_shipping_line_validation to ensure duplicate shipping lines are not allowed.
        """
        location_inv_setting = self.env["location.invoice.setting"].create(
            {
                "company_id": self.company.id,
                "inv_shipping_line_id": self.shipping_line.id,
            }
        )
        with self.assertRaises(ValidationError, msg="Shipping Line is already mapped"):
            self.env["location.invoice.setting"].create(
                {
                    "company_id": self.company.id,
                    "inv_shipping_line_id": self.shipping_line.id,
                }
            )

    def test_compute_inv_shipping_line_domain(self):
        """
        Test _compute_inv_shipping_line_domain to ensure the domain is computed correctly.
        """
        location_shipping_line = self.env["location.shipping.line.mapping"].create(
            {
                "shipping_line_id": self.shipping_line.id,
                "company_id": self.company.id,
            }
        )
        location_inv_setting = self.env["location.invoice.setting"].create(
            {
                "company_id": self.company.id,
                "inv_shipping_line_id": self.shipping_line.id,
            }
        )
        location_inv_setting._compute_inv_shipping_line_domain()
        self.assertIn(
            self.shipping_line.id,
            location_inv_setting.inv_shipping_line_domain.ids,
            "Shipping line should be in the computed domain.",
        )

    #
    def test_get_create_record_info(self):
        """
        Test _get_create_record_info to ensure it correctly sets the creation record information.
        """
        self.env.user.tz = "UTC"
        user = self.env["res.users"].create(
            {
                "name": "Test User",
                "login": "test_user",
                "company_ids": [(4, self.company.id)],
                "company_id": self.company.id,
                "tz": "UTC",
            }
        )
        location_inv_setting = (
            self.env["location.invoice.setting"]
            .with_user(user)
            .create(
                {
                    "company_id": self.company.id,
                }
            )
        )
        location_inv_setting._get_create_record_info()
        self.assertTrue(
            location_inv_setting.display_create_info, "The creation info should be set."
        )

    def test_get_create_record_info_no_timezone(self):
        """
        Test _get_create_record_info to ensure it correctly sets the creation record information.
        """
        self.env.user.tz = False
        user = self.env["res.users"].create(
            {
                "name": "Test User",
                "login": "test_user",
                "company_ids": [(4, self.company.id)],
                "company_id": self.company.id,
                "tz": False,
            }
        )
        location_inv_setting = (
            self.env["location.invoice.setting"]
            .with_user(user)
            .create(
                {
                    "company_id": self.company.id,
                }
            )
        )
        location_inv_setting._get_create_record_info()
        self.assertEqual(location_inv_setting.display_create_info, "")

    def test_get_modify_record_info(self):
        """
        Test _get_modify_record_info to ensure it correctly sets the modification record information.
        """
        self.env.user.tz = "UTC"
        location_inv_setting = self.env["location.invoice.setting"].create(
            {
                "company_id": self.company.id,
                "inv_applicable_at_location_ids": [(6, 0, [self.lift_on_option.id])],
            }
        )
        location_inv_setting.write(
            {
                "inv_applicable_at_location_ids": [(6, 0, [self.lift_off_option.id])],
            }
        )
        location_inv_setting._get_modify_record_info()
        self.assertTrue(
            location_inv_setting.display_modified_info,
            "The modification info should be set.",
        )

    def test_get_modify_record_info_no_timezone(self):
        """
        Test _get_modify_record_info to ensure it correctly sets the modification record information.
        """
        self.env.user.tz = False
        location_inv_setting = self.env["location.invoice.setting"].create(
            {
                "company_id": self.company.id,
                "inv_applicable_at_location_ids": [(6, 0, [self.lift_on_option.id])],
            }
        )
        location_inv_setting.write(
            {
                "inv_applicable_at_location_ids": [(6, 0, [self.lift_off_option.id])],
            }
        )
        location_inv_setting._get_modify_record_info()
        self.assertEqual(
            location_inv_setting.display_modified_info,
            "",
        )

    def test_check_pincode_validation(self):
        """
        Test _check_pincode_validation to ensure only numeric pincodes are allowed.
        """
        location_inv_setting = self.env["location.invoice.setting"].create(
            {"company_id": self.company.id, "pincode": "12345"}
        )

        # Valid pincode should not raise ValidationError
        location_inv_setting._check_pincode_validation()
        self.assertEqual(
            location_inv_setting.pincode, "12345", "Pincode should be '12345'."
        )

        # Non-numeric pincode should raise ValidationError

        with self.assertRaises(
            ValidationError, msg="The Pincode must contain only numeric values."
        ):
            location_inv_setting.pincode = "ABC123"

    def test_get_payment_mode_values(self):
        """
        Test _get_payment_mode_values to ensure it sets payment_mode correctly.
        """
        location_inv_setting = self.env["location.invoice.setting"].create(
            {
                "company_id": self.company.id,
                "payment_mode_ids": [
                    (6, 0, [self.payment_mode_cash.id, self.payment_mode_online.id])
                ],
            }
        )
        location_inv_setting._get_payment_mode_values()
        self.assertEqual(
            location_inv_setting.payment_mode,
            "Cash, Online",
            "payment_mode should be set to 'Cash, Online'.",
        )

        # Test with only cash payment mode
        location_inv_setting.payment_mode_ids = [(6, 0, [self.payment_mode_cash.id])]
        location_inv_setting._get_payment_mode_values()
        self.assertEqual(
            location_inv_setting.payment_mode,
            "Cash",
            "payment_mode should be set to 'Cash'.",
        )

        # Test with no payment modes
        location_inv_setting.payment_mode_ids = [(6, 0, [])]
        location_inv_setting._get_payment_mode_values()
        self.assertFalse(
            location_inv_setting.payment_mode,
            "payment_mode should be False when no modes are selected.",
        )

    def test_get_inv_applicable_values(self):
        """
        Test _get_inv_applicable_values to ensure it sets inv_applicable_at_location correctly.
        """
        location_inv_setting = self.env["location.invoice.setting"].create(
            {
                "company_id": self.company.id,
                "inv_applicable_at_location_ids": [
                    (6, 0, [self.lift_on_option.id, self.lift_off_option.id])
                ],
            }
        )
        location_inv_setting._get_inv_applicable_values()
        self.assertEqual(
            location_inv_setting.inv_applicable_at_location,
            "Lift Off, Lift On",
            "inv_applicable_at_location should be set to 'Lift Off, Lift On'.",
        )

        # Test with additional 'Others' option
        location_inv_setting.inv_applicable_at_location_ids = [
            (
                6,
                0,
                [
                    self.lift_on_option.id,
                    self.lift_off_option.id,
                    self.others_option.id,
                ],
            )
        ]
        location_inv_setting._get_inv_applicable_values()
        self.assertEqual(
            location_inv_setting.inv_applicable_at_location,
            "Lift Off, Lift On, Others",
            "inv_applicable_at_location should be set to 'Lift Off, Lift On, Others'.",
        )

        # Test with no applicable options
        location_inv_setting.inv_applicable_at_location_ids = [(6, 0, [])]
        location_inv_setting._get_inv_applicable_values()
        self.assertFalse(
            location_inv_setting.inv_applicable_at_location,
            "inv_applicable_at_location should be False when no options are selected.",
        )

    def test_onchange_company_name_in_inv(self):
        """
        Test onchange_company_name_in_inv to check the address fields update.
        """
        location_inv_setting = self.env["location.invoice.setting"].create(
            {"company_id": self.company.id, "company_name_in_inv": "others"}
        )
        location_inv_setting.onchange_company_name_in_inv()
        self.assertFalse(
            location_inv_setting.country_id,
            "Country should be cleared when company name is set to others.",
        )
        self.assertFalse(
            location_inv_setting.address_line_1,
            "Address Line 1 should be cleared when company name is set to others.",
        )
        self.assertFalse(
            location_inv_setting.address_line_2,
            "Address Line 2 should be cleared when company name is set to others.",
        )
        self.assertFalse(
            location_inv_setting.city,
            "City should be cleared when company name is set to others.",
        )
        self.assertFalse(
            location_inv_setting.state_id,
            "State should be cleared when company name is set to others.",
        )
        self.assertFalse(
            location_inv_setting.pincode,
            "Pincode should be cleared when company name is set to others.",
        )

        # Test when company name is set to same_as_company
        location_inv_setting.company_name_in_inv = "same_as_company"
        location_inv_setting.onchange_company_name_in_inv()
        main_company = self.env["res.company"].search(
            [("parent_id", "=", False)], limit=1
        )
        if main_company:
            self.assertEqual(
                location_inv_setting.country_id.id,
                main_company.country_id.id if main_company.country_id else False,
                "Country should be set to main company's country.",
            )
            self.assertEqual(
                location_inv_setting.state_id.id,
                main_company.state_id.id if main_company.state_id else False,
                "State should be set to main company's state.",
            )
        if location_inv_setting.company_id:
            self.assertEqual(
                location_inv_setting.address_line_1,
                location_inv_setting.company_id.street,
                "Address Line 1 should be set to current company's street.",
            )
            self.assertEqual(
                location_inv_setting.address_line_2,
                location_inv_setting.company_id.street2,
                "Address Line 2 should be set to current company's street2.",
            )
            self.assertEqual(
                location_inv_setting.city,
                location_inv_setting.company_id.city,
                "City should be set to current company's city.",
            )
            self.assertEqual(
                location_inv_setting.pincode,
                location_inv_setting.company_id.zip,
                "Pincode should be set to current company's zip.",
            )
