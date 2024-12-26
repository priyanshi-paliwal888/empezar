from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestResGroups(TransactionCase):

    def setUp(self):
        super().setUp()
        self.res_groups_model = self.env["res.groups"]
        self.user_model = self.env["res.users"]

    def test_check_active_records(self):
        # Create a new group record
        group = self.res_groups_model.create({"name": "Test Group", "active": True})
        # Check if the rec_status is computed correctly
        self.assertEqual(group.rec_status, "active")

        # Deactivate the group
        group.active = False
        group._check_active_records()
        self.assertEqual(group.rec_status, "disable")

    def test_get_create_record_info(self):
        # Create a new group record
        group = self.res_groups_model.create({"name": "Test Group", "active": True})
        self.env.user.tz = "UTC"
        # Check if display_create_info is computed correctly
        if group.env.user.tz and group.create_uid:
            tz_create_date = group.env.user.sudo().convert_datetime_to_user_timezone(
                group.create_date
            )
            create_uid_name = group.create_uid.name
            if tz_create_date:
                expected_info = group.env.user.sudo().get_user_log_data(
                    tz_create_date, create_uid_name
                )
                self.assertEqual(group.display_create_info, expected_info)
        else:
            self.assertEqual(group.display_create_info, "")

    def test_get_create_record_info_no_timezone(self):
        # Create a new group record
        group = self.res_groups_model.create({"name": "Test Group", "active": True})
        self.env.user.tz = False
        # Check if display_create_info is computed correctly
        group.env.user.tz = False
        self.assertEqual(group.display_create_info, "")

    def test_get_modify_record_info(self):
        # Create a new group record
        group = self.res_groups_model.create({"name": "Test Group", "active": True})
        self.env.user.tz = "UTC"
        # Modify the record
        group.name = "Updated Test Group"
        group._get_modify_record_info()
        # Check if display_modified_info is computed correctly
        if group.env.user.tz and group.write_uid:
            tz_write_date = group.env.user.sudo().convert_datetime_to_user_timezone(
                group.write_date
            )
            write_uid_name = group.write_uid.name
            if tz_write_date:
                expected_info = group.env.user.sudo().get_user_log_data(
                    tz_write_date, write_uid_name
                )
                self.assertEqual(group.display_modified_info, expected_info)
        else:
            self.assertEqual(group.display_modified_info, "")

    def test_get_modify_record_info_no_timezone(self):
        group = self.res_groups_model.create({"name": "Test Group", "active": True})
        self.env.user.tz = False
        # Modify the record
        group.name = "Updated Test Group"
        group.env.user.tz = False
        group._get_modify_record_info()
        self.assertEqual(group.display_modified_info, "")

    def test_check_contact_no_valid(self):
        user = self.user_model.create(
            {
                "name": "Test User",
                "login": "test",
                "mobile": "1884567890",  # Valid mobile number
            }
        )
        self.assertEqual(user.mobile, "1884567890")

    def test_check_contact_no_invalid_characters(self):
        with self.assertRaises(ValidationError) as e:
            self.user_model.create(
                {
                    "name": "Invalid User",
                    "login": "invalid1",
                    "mobile": "123456abc",  # Invalid characters
                }
            )
        self.assertEqual(
            str(e.exception), "Invalid contact number. Only Numeric values allow."
        )

    def test_check_contact_no_exceeds_length(self):
        with self.assertRaises(ValidationError) as e:
            self.user_model.create(
                {
                    "name": "Invalid User",
                    "login": "invalid2",
                    "mobile": "123456789012",  # More than 10 digits
                }
            )
        self.assertEqual(
            str(e.exception), "Invalid contact number. Maximum 10 digits allow."
        )

    def test_check_contact_no_duplicate(self):
        # Create a user with a valid mobile number
        self.user_model.create(
            {
                "name": "First User",
                "mobile": "1234567890",
                "login": "first",
            }
        )
        # Attempt to create another user with the same mobile number
        with self.assertRaises(ValidationError) as e:
            self.user_model.create(
                {
                    "name": "Second User",
                    "login": "Second",
                    "mobile": "1234567890",
                }
            )
        self.assertEqual(str(e.exception), "Contact number already exists !")
