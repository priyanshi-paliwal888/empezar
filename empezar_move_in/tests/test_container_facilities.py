from odoo.tests.common import TransactionCase


class TestContainerFacilities(TransactionCase):

    def setUp(self):
        super().setUp()

        self.master_port_data_model = self.env["master.port.data"]
        # Create a master port data for testing
        self.port = self.master_port_data_model.create(
            {
                "country_iso_code": "US",
                "port_code": "TESTPORT",
                "port_name": "Test Port",
                "state_code": "NY",
                "status": "Active",
                "latitude": "40.7128° N",
                "longitude": "74.0060° W",
                "popular_port": True,
                "active": True,
            }
        )
        self.test_company = self.env["res.company"].create(
            {
                "name": "Test Company",
            }
        )
        # Create a sample facility type for testing if needed
        self.facility = self.env["container.facilities"].create(
            {
                "name": "Test Facility Modify Info",
                "facility_type": "empty_yard",
                "code": "MODIFY_INFO",
                "port": self.port.id,
                "company_id": self.test_company.id,
            }
        )

    def test_default_get_without_context(self):
        """Test default_get without any specific context."""
        facility_model = self.env["container.facilities"]

        # Call default_get without context
        default_vals = facility_model.default_get(["facility_type"])

        # Check that no facility type is set by default
        self.assertFalse(
            default_vals.get("facility_type"),
            "Facility type should not be set without context",
        )

    def test_default_get_with_cfs_context(self):
        """Test default_get with is_from_move_in and cfs_move_in in context."""
        facility_model = self.env["container.facilities"].with_context(
            is_from_move_in=True, cfs_move_in=True
        )

        # Call default_get with context for CFS
        default_vals = facility_model.default_get(["facility_type"])

        # Check that facility_type is set to 'cfs'
        self.assertEqual(
            default_vals.get("facility_type"),
            "cfs",
            "Facility type should be set to 'cfs'",
        )

    def test_default_get_with_terminal_context(self):
        """Test default_get with is_from_move_in and terminal_move_in in context."""
        facility_model = self.env["container.facilities"].with_context(
            is_from_move_in=True, terminal_move_in=True
        )

        # Call default_get with context for Terminal
        default_vals = facility_model.default_get(["facility_type"])

        # Check that facility_type is set to 'terminal'
        self.assertEqual(
            default_vals.get("facility_type"),
            "terminal",
            "Facility type should be set to 'terminal'",
        )

    def test_default_get_with_empty_yard_context(self):
        """Test default_get with is_from_move_in and empty_yard_move_in in context."""
        facility_model = self.env["container.facilities"].with_context(
            is_from_move_in=True, empty_yard_move_in=True
        )

        # Call default_get with context for Empty Yard
        default_vals = facility_model.default_get(["facility_type"])

        # Check that facility_type is set to 'empty_yard'
        self.assertEqual(
            default_vals.get("facility_type"),
            "empty_yard",
            "Facility type should be set to 'empty_yard'",
        )
