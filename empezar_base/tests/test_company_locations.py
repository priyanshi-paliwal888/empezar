from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestResCompanyLocation(TransactionCase):

    def setUp(self):
        super().setUp()
        # Create a test user with specific timezone
        self.user_tz = self.env["res.users"].create(
            {
                "name": "Test User TZ",
                "login": "test_user_tz",
                "email": "test_tz@example.com",
                "company_id": self.env.company.id,
                "tz": "Europe/Paris",
            }
        )

        # Create a test company
        self.test_company = self.env["res.company"].create(
            {
                "name": "Test Company",
                "location_code": "TC1",
                "location_type": "cfs",
                "port": self.env["master.port.data"]
                .create(
                    {
                        "country_iso_code": "FR",
                        "port_code": "PAR",
                        "port_name": "Paris Port",
                    }
                )
                .id,
                "capacity": 100,
            }
        )

    def test_create_company(self):
        """Test the creation of a company record"""
        self.assertEqual(
            self.test_company.name,
            "Test Company",
            "Company name should be 'Test Company'",
        )
        self.assertEqual(
            self.test_company.location_code,
            "TC1",
            "Company location code should be 'TC1'",
        )
        self.assertEqual(
            self.test_company.location_type,
            "cfs",
            "Company location type should be 'CFS'",
        )
        self.assertEqual(
            int(self.test_company.capacity), 100, "Company capacity should be 100"
        )

    def test_unique_location_code_constraint(self):
        """Test the unique constraint on location code"""
        with self.assertRaises(ValidationError):
            self.env["res.company"].create(
                {
                    "name": "Another Company",
                    "location_code": "TC1",  # Same location code as self.test_company
                    "location_type": "terminal",
                    "port": self.env["master.port.data"]
                    .create(
                        {
                            "country_iso_code": "US",
                            "port_code": "LAX",
                            "port_name": "Los Angeles Port",
                        }
                    )
                    .id,
                    "capacity": 200,
                }
            )

    #
    def test_display_create_info(self):
        """Test the display of create record info"""
        self.env.user.tz = "UTC"
        self.test_company._get_create_record_info()
        self.assertTrue(
            self.test_company.display_create_info, "Create info should be displayed"
        )

    def test_display_modified_info(self):
        """Test the display of modified record info"""
        self.env.user.tz = "UTC"
        self.test_company.write({"name": "Updated Test Company"})
        self.test_company._get_modify_record_info()
        self.assertTrue(self.test_company.display_modified_info)

    def test_active_record_status(self):
        """Test the computed field for active record status"""
        self.assertEqual(
            self.test_company.rec_status,
            "active",
            "The record status should be active by default",
        )

    def test_default_get_company(self):
        """Test default get method for a new company record"""
        default_vals = (
            self.env["res.company"]
            .with_context(is_res_company_location_view=True)
            .default_get([])
        )
        self.assertEqual(
            default_vals.get("parent_id"),
            self.env.ref("base.main_company").id,
            "Default parent_id should be main company",
        )
        self.assertEqual(
            default_vals.get("country_id"),
            self.env.ref("base.main_company").country_id.id,
            "Default country_id should be main company country",
        )

    def test_check_active_records(self):
        """Test the method to check active records"""
        # Assuming check_active_records method in ContainerTypeEdi changes status to 'disable'
        self.test_company._check_active_records()
        self.assertEqual(
            self.test_company.rec_status,
            "active",
            "The record status should remain active",
        )
