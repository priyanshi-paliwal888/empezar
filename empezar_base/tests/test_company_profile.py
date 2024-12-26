import os
from odoo.tests import common
from odoo.exceptions import ValidationError


class TestResCompany(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.company_model = self.env["res.company"]
        self.country = self.env["res.country"].search([("code", "=", "IN")])
        self.state = self.env["res.country.state"].search([("code", "=", "KA")])
        self.company = self.env["res.company"].create(
            {
                "name": "Test Company setup",
                "country_id": self.country.id,
                "state_id": self.state.id,
                "email": "test@example.com",
                "escalation_email": "escalation@example.com",
                "pan": "ABCDE1234F",
                "cin": "L12345MH1987PLC123456",
                "capacity": 100,
            }
        )

    def test_create_company(self):
        """Test creating a company with valid data"""
        image_path = (
            os.path.join(os.path.dirname(__file__)) + "/img/sample_img_500kb.png"
        )
        with open(image_path, "rb") as f:
            image_data = f.read()
        company = self.company_model.create(
            {
                "name": "Test Company",
                "country_id": self.env.ref(
                    "base.in"
                ).id,  # Assuming India with code 'IN'
                "street": "123 Main Street",
                "city": "Anytown",
                "zip": "945738",
                "email": "test@example.com",
                "phone": "5555555555",
                "currency_id": self.env.ref("base.USD").id,
                "date_format": "YYYY/MM/DD",
                "report_no_of_days": 100,
                "pan": "ABCDE01234",
                "cin": "ABCDEF1234567890OPQRS",
                "street2": "street2",
                "logo": image_data,
            }
        )

        # Check that the company record was created successfully
        self.assertEqual(company.name, "Test Company")
        self.assertEqual(company.country_id.code, "IN")

    def test_create_company_other_country_does_not_set_is_country_india(self):
        """Test that selecting a non-India country does not change is_country_india."""
        other_country = self.env["res.country"].search([("code", "=", "US")], limit=1)
        company = self.company_model.create(
            {
                "name": "Test Company",
                "country_id": other_country.id,  # Assuming India with code 'IN'
                "street": "123 Main Street",
                "city": "Anytown",
                "zip": "12345",
                "email": "test@example.com",
                "phone": "5555555555",
                "currency_id": self.env.ref("base.USD").id,
                "date_format": "YYYY/MM/DD",
            }
        )
        company._check_is_country_india()
        # Simulate selecting a non-India country (replace with a different code)
        self.assertEqual(company.is_country_india, False)  # Remains False

    def test_create_company_invalid_report_days(self):
        with self.assertRaises(ValidationError) as e:
            self.company_model.create(
                {
                    "name": "Test Company",
                    "country_id": self.env.ref(
                        "base.in"
                    ).id,  # Assuming India with code 'IN'
                    "street": "123 Main Street",
                    "city": "Anytown",
                    "zip": "12345",
                    "email": "test@example.com",
                    "phone": "5555555555",
                    "currency_id": self.env.ref("base.USD").id,
                    "date_format": "YYYY/MM/DD",
                    "report_no_of_days": 90000,
                }
            )
        self.assertEqual(e.exception.args[0], "Allow Value between 0 to 9999")

    def test_create_company_invalid_pan_length(self):
        """Test that a PAN number with incorrect length raises a ValidationError."""
        with self.assertRaises(ValidationError) as e:
            self.company_model.create(
                {
                    "name": "Test Company",
                    "country_id": self.env.ref(
                        "base.in"
                    ).id,  # Assuming India with code 'IN'
                    "street": "123 Main Street",
                    "city": "Anytown",
                    "zip": "12345",
                    "email": "test@example.com",
                    "phone": "5555555555",
                    "currency_id": self.env.ref("base.USD").id,
                    "date_format": "YYYY/MM/DD",
                    "pan": "ABCD1234",
                }
            )

        self.assertEqual(e.exception.args[0], "Pan Number should be 10 characters long")

    def test_create_company_invalid_pan_characters(self):
        """Test that a PAN number with non-alphanumeric characters raises a ValidationError."""
        with self.assertRaises(ValidationError) as e:
            self.company_model.create(
                {
                    "name": "Test Company",
                    "country_id": self.env.ref(
                        "base.in"
                    ).id,  # Assuming India with code 'IN'
                    "street": "123 Main Street",
                    "city": "Anytown",
                    "zip": "12345",
                    "email": "test@example.com",
                    "phone": "5555555555",
                    "currency_id": self.env.ref("base.USD").id,
                    "date_format": "YYYY/MM/DD",
                    "pan": "ABC@DEFGHI",
                }
            )
        self.assertEqual(e.exception.args[0], "Please Enter Alphanumeric Value")

    def test_create_company_invalid_cin_length(self):
        """Test that a CIN number with incorrect length raises a ValidationError."""
        with self.assertRaises(ValidationError) as e:
            self.company_model.create(
                {
                    "name": "Test Company",
                    "country_id": self.env.ref(
                        "base.in"
                    ).id,  # Assuming India with code 'IN'
                    "street": "123 Main Street",
                    "city": "Anytown",
                    "zip": "12345",
                    "email": "test@example.com",
                    "phone": "5555555555",
                    "currency_id": self.env.ref("base.USD").id,
                    "date_format": "YYYY/MM/DD",
                    "cin": "ABCD1234",
                }
            )
        self.assertEqual(e.exception.args[0], "CIN Number should be 21 characters long")

    def test_create_company_invalid_cin_characters(self):
        """Test that a CIN number with non-alphanumeric characters raises a ValidationError."""
        with self.assertRaises(ValidationError) as e:
            self.company_model.create(
                {
                    "name": "Test Company",
                    "country_id": self.env.ref(
                        "base.in"
                    ).id,  # Assuming India with code 'IN'
                    "street": "123 Main Street",
                    "city": "Anytown",
                    "zip": "12345",
                    "email": "test@example.com",
                    "phone": "5555555555",
                    "currency_id": self.env.ref("base.USD").id,
                    "date_format": "YYYY/MM/DD",
                    "cin": "QAZXSWEDCVF@TGBNHYUJM",
                }
            )
        self.assertEqual(e.exception.args[0], "Please Enter Alphanumeric Value")

    def test_create_company_invalid_name(self):
        """Test creating a company with an invalid name (too short)"""
        with self.assertRaises(ValidationError) as e:
            self.company_model.create(
                {
                    "name": "AB",  # Name is less than 3 characters
                    "country_id": self.env.ref("base.in").id,
                    "street": "123 Main Street",
                    "city": "Anytown",
                    "zip": "12345",
                    "email": "test@example.com",
                    "phone": "5555555555",
                    "currency_id": self.env.ref("base.USD").id,
                    "date_format": "YYYY/MM/DD",
                }
            )
        self.assertEqual(
            e.exception.args[0], "Minimum 3 characters and maximum 128 characters allow"
        )
        # with self.assertRaises(ValidationError) as e:
        #     company._check_name_validation()
        # self.assertEqual(e.exception.args[0], "Minimum 3 characters and maximum 128 characters allow")

    def test_create_company_invalid_city_length(self):
        """Test that a city with more than 72 characters raises a ValidationError."""
        long_city_name = "This is a very long city name that exceeds the 72 character limit Test City Name."
        with self.assertRaises(ValidationError) as e:
            self.company_model.create(
                {
                    "name": "Test Company",
                    "country_id": self.env.ref("base.in").id,
                    "street": "123 Main Street",
                    "email": "test@example.com",
                    "phone": "5555555555",
                    "currency_id": self.env.ref("base.USD").id,
                    "date_format": "YYYY/MM/DD",
                    "city": long_city_name,
                }
            )

        self.assertEqual(e.exception.args[0], "Maximum 72 characters allow")

    def test_create_company_invalid_street_length(self):
        """Test that a city with more than 72 characters raises a ValidationError."""
        long_street_name = "This is a very long Stret name that exceeds the 128 character limit Test Street Name.This is a very long Stret name that exceeds the 128 character limit Test Street Name."
        with self.assertRaises(ValidationError) as e:
            self.company_model.create(
                {
                    "name": "Test Company",
                    "country_id": self.env.ref("base.in").id,
                    "city": "Anytown",
                    "email": "test@example.com",
                    "phone": "5555555555",
                    "currency_id": self.env.ref("base.USD").id,
                    "date_format": "YYYY/MM/DD",
                    "street": long_street_name,
                }
            )

        self.assertEqual(e.exception.args[0], "Maximum 128 characters allow")

    def test_create_company_invalid_street2_length(self):
        long_street_name = "This is a very long Stret2 name that exceeds the 128 character limit Test Street Name.This is a very long street2 name that exceeds the 128 character limit Test Street2 Name."
        with self.assertRaises(ValidationError) as e:
            self.company_model.create(
                {
                    "name": "Test Company",
                    "country_id": self.env.ref("base.in").id,
                    "street": "123 Main Street",
                    "city": "Anytown",
                    "email": "test@example.com",
                    "phone": "5555555555",
                    "currency_id": self.env.ref("base.USD").id,
                    "date_format": "YYYY/MM/DD",
                    "street2": long_street_name,
                }
            )

        self.assertEqual(e.exception.args[0], "Maximum 128 characters allow")

    def test_invalid_logo_size(self):
        image_path = os.path.join(os.path.dirname(__file__)) + "/img/sample_img_2mb.png"
        with open(image_path, "rb") as f:
            image_data = f.read()
        with self.assertRaises(ValidationError) as e:
            self.company_model.create(
                {
                    "name": "Test Company",
                    "country_id": self.env.ref("base.in").id,
                    "street": "123 Main Street",
                    "city": "Anytown",
                    "email": "test@example.com",
                    "phone": "5555555555",
                    "currency_id": self.env.ref("base.USD").id,
                    "date_format": "YYYY/MM/DD",
                    "logo": image_data,
                }
            )
        self.assertEqual(e.exception.args[0], "Image size cannot exceed 1MB.")

    def test_create_company_invalid_email(self):
        """Test creating a company with an invalid email"""
        with self.assertRaises(ValidationError) as e:
            self.company_model.create(
                {
                    "name": "Test Company",
                    "country_id": self.env.ref("base.in").id,
                    "street": "123 Main Street",
                    "city": "Anytown",
                    "zip": "123456789012345",
                    "email": "invalid_email",  # invalid Email
                    "phone": "5555555555",
                    "currency_id": self.env.ref("base.USD").id,
                    "date_format": "YYYY/MM/DD",
                }
            )
        self.assertEqual(
            e.exception.args[0],
            "Invalid email address. Please enter correct email address.",
        )

    def test_email_validation_valid(self):
        self.company.email = "valid@example.com"
        self.company.is_valid_email()  # Should pass without exception

    def test_email_validation_invalid(self):
        with self.assertRaises(ValidationError):
            self.company.email = "invalid-email"
            self.company.is_valid_email()

    def test_escalation_email_validation_valid(self):
        self.company.escalation_email = "valid1@example.com, valid2@example.com"
        self.company._check_email_ids()  # Should pass without exception

    def test_escalation_email_validation_invalid(self):
        with self.assertRaises(ValidationError):
            self.company.escalation_email = "invalid-email"
            self.company._check_email_ids()

    def test_onchange_state_id_valid(self):
        self.company.country_id = self.country.id
        self.company.state_id = self.state.id
        self.company.write({"state_id": self.state.id})
        warning = self.company.with_context(
            {"is_res_company_location_view": True}
        ).onchange_state_id()
        self.assertIsNone(warning)  # No warning expected

    def test_check_shipping_line_capacity_valid(self):
        """Test that the capacity check passes with valid capacities"""

        # Create a shipping line mapping with capacity within the location's limit
        shipping_line_mapping = self.env["location.shipping.line.mapping"].create(
            {
                "shipping_line_id": self.env["res.partner"]
                .create({"name": "Shipping Line 1", "is_company": True})
                .id,
                "capacity": 50,
                "active": True,
                "company_id": self.company.id,
            }
        )

        self.company.write(
            {"shipping_line_mapping_ids": [(4, shipping_line_mapping.id)]}
        )

        # No ValidationError should be raised
        self.company.check_shipping_line_capacity()

    def test_check_shipping_line_capacity_invalid(self):
        """Test that the capacity check raises a ValidationError with invalid capacities"""

        # Create a shipping line mapping with capacity exceeding the location's limit
        shipping_line_mapping = self.env["location.shipping.line.mapping"].create(
            {
                "shipping_line_id": self.env["res.partner"]
                .create({"name": "Shipping Line 2", "is_company": True})
                .id,
                "capacity": 200,
                "active": True,
                "company_id": self.company.id,
            }
        )

        self.company.write(
            {"shipping_line_mapping_ids": [(4, shipping_line_mapping.id)]}
        )

        with self.assertRaises(ValidationError) as e:
            self.company.check_shipping_line_capacity()

        self.assertEqual(
            e.exception.args[0], "Capacity Added exceeds the location capacity"
        )

    def test_phone_numeric_validation_valid(self):
        """Test valid phone number"""
        valid_phone = "1234567890"  # Example valid phone number

        try:
            self.company.phone = valid_phone
        except ValidationError:
            self.fail(
                f"_phone_numeric_validation raised ValidationError unexpectedly for valid phone number: {valid_phone}"
            )

    def test_phone_numeric_validation_invalid(self):
        """Test invalid phone number"""
        invalid_phone = "abcdefg"  # Example invalid phone number

        with self.assertRaises(ValidationError) as e:
            self.company.phone = invalid_phone

        self.assertEqual(
            e.exception.args[0],
            "The phone number must contain only numeric values.",
            f"Expected ValidationError message does not match: {e.exception.args[0]}",
        )

    def test_check_zip_validation_valid(self):
        """Test valid ZIP code"""
        valid_zip = "12345"  # Example valid ZIP code

        try:
            self.company.zip = valid_zip
        except ValidationError:
            self.fail(
                f"_check_zip_validation raised ValidationError unexpectedly for valid ZIP code: {valid_zip}"
            )

    def test_check_zip_validation_invalid(self):
        """Test invalid ZIP code"""
        invalid_zip = "abcdefg"  # Example invalid ZIP code

        with self.assertRaises(ValidationError) as e:
            self.company.zip = invalid_zip

        self.assertEqual(
            e.exception.args[0],
            "The Pincode must contain only numeric values.",
            f"Expected ValidationError message does not match: {e.exception.args[0]}",
        )
