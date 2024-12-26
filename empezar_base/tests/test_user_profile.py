from unittest.mock import patch
from odoo.tests import common
from odoo.exceptions import ValidationError


class TestResUsersProfile(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.user_record = self.env["res.users"].create(
            {
                "name": "Test User",
                "login": "test_user",
            }
        )

    def test_valid_email(self):
        self.user_record.email = "test@example.com"
        self.assertTrue(self.user_record)  # No exception raised

    def test_invalid_email_format(self):
        with self.assertRaises(ValidationError) as e:
            self.user_record.email = "invalid_email"
        self.assertEqual(
            e.exception.args[0],
            "Invalid email address. Please enter correct email address.",
        )

    def test_email_length_exceeded(self):
        long_email = "a" * 57 + "@example.com"
        with self.assertRaises(ValidationError) as e:
            self.user_record.email = long_email
        self.assertEqual(e.exception.args[0], "Email cannot exceed 56 characters")

    # def test_valid_phone_number(self):
    #     self.user_record.mobile='1234567890'
    #     self.assertTrue(self.user_record)  # No exception raised

    def test_invalid_phone_number_format(self):
        with self.assertRaises(ValidationError) as e:
            self.user_record.mobile = "invalid_number"
        self.assertEqual(
            e.exception.args[0], "Invalid contact number. Only Numeric values allow."
        )

    def test_phone_number_length_exceeded(self):
        with self.assertRaises(ValidationError) as e:
            long_number = "12345678901"
            self.user_record.mobile = long_number
        self.assertEqual(
            e.exception.args[0], "Invalid contact number. Maximum 10 digits allow."
        )

    def test_duplicate_phone_number(self):
        with self.assertRaises(ValidationError) as e:
            self.user_record.mobile = 1234567890
            user2 = self.env["res.users"].create(
                {
                    "name": "User2",
                    "login": "User2",
                }
            )
            user2.mobile = 1234567890
        self.assertEqual(e.exception.args[0], "Contact number already exists !")

    def test_valid_username_length(self):
        self.user_record.login = "test_user"
        self.assertTrue(self.user_record)  # No exception raised

    def test_username_length_exceeded(self):
        long_username = "a" * 57
        with self.assertRaises(ValidationError) as e:
            self.user_record.login = long_username
        self.assertEqual(e.exception.args[0], "Username cannot exceed 56 characters")

    def test_user_status_active(self):
        """Test if user status is 'active' when active is True."""
        self.user_record.active = True
        self.user_record._check_user_status()
        self.assertEqual(self.user_record.user_status, "active")

    def test_user_status_inactive(self):
        """Test if user status is 'inactive' when active is False."""
        self.user_record.active = False
        self.user_record._check_user_status()
        self.assertEqual(self.user_record.user_status, "inactive")

    def test_create_record_info(self):
        """Test if creation log information is correctly populated."""
        self.user_record.tz = "UTC"
        self.user_record.display_create_info = ""
        with patch(
            "odoo.addons.empezar_base.models.res_users.ResUsers.convert_datetime_to_user_timezone"
        ) as mock_convert:
            mock_convert.return_value = (
                self.user_record.create_date
            )  # Mock the timezone conversion
            self.user_record._get_create_record_info()
            self.assertTrue(
                self.user_record.display_create_info, "The creation info should be set."
            )

    def test_modify_record_info(self):
        """Test if modification log information is correctly populated."""
        self.user_record.tz = "UTC"
        self.user_record.display_modified_info = ""
        self.user_record.write({"name": "Modified User"})
        with patch(
            "odoo.addons.empezar_base.models.res_users.ResUsers.convert_datetime_to_user_timezone"
        ) as mock_convert:
            mock_convert.return_value = (
                self.user_record.write_date
            )  # Mock the timezone conversion
            self.user_record._get_modify_record_info()
            self.assertTrue(
                self.user_record.display_modified_info,
                "The modification info should be set.",
            )
