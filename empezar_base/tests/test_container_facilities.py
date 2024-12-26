from odoo.tests.common import TransactionCase


class TestContainerFacilities(TransactionCase):

    def setUp(self):
        super().setUp()
        self.container_facilities_model = self.env["container.facilities"]
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

    def test_create_container_facility(self):
        # Create a new container facility
        facility_data = {
            "name": "Test Facility",
            "facility_type": "terminal",
            "code": "TF001",
            "port": self.port.id,
            "active": True,
        }
        facility = self.container_facilities_model.create(facility_data)
        # Check if the facility is created successfully
        self.assertTrue(facility)

    def test_check_active_records(self):
        # Create a new container facility
        facility_data = {
            "name": "Test Facility",
            "facility_type": "terminal",
            "code": "TF001",
            "port": self.port.id,
            "active": True,
        }
        facility = self.container_facilities_model.create(facility_data)
        # Check if the rec_status is computed correctly
        self.assertEqual(facility.rec_status, "active")

        # Deactivate the facility
        facility.active = False
        facility._check_active_records()
        self.assertEqual(facility.rec_status, "disable")

    def test_get_create_record_info(self):
        """
        Test _get_create_record_info to ensure it correctly sets the creation record information.
        """
        self.env.user.tz = "UTC"
        user = self.env.user

        # Create a Container Facility record
        facility = self.env["container.facilities"].create(
            {
                "name": "Test Facility Create Info",
                "facility_type": "empty_yard",
                "code": "CREATE_INFO",
                "port": self.port.id,
                "company_id": self.test_company.id,
            }
        )

        # Call the method to compute the creation info
        facility._get_create_record_info()
        self.assertTrue(
            facility.display_create_info, "The creation info should be set."
        )
        self.assertIn(
            user.name,
            facility.display_create_info,
            "Creation info should include the user name.",
        )

    def test_get_modify_record_info(self):
        """
        Test _get_modify_record_info to ensure it correctly sets the modification record information.
        """
        self.env.user.tz = "UTC"
        user = self.env.user

        # Create a Container Facility record
        facility = self.env["container.facilities"].create(
            {
                "name": "Test Facility Modify Info",
                "facility_type": "empty_yard",
                "code": "MODIFY_INFO",
                "port": self.port.id,
                "company_id": self.test_company.id,
            }
        )

        # Modify the record to trigger the write_uid and write_date updates
        facility.write({"name": "Updated Facility Name"})

        # Call the method to compute the modification info
        facility._get_modify_record_info()
        self.assertTrue(
            facility.display_modified_info, "The modification info should be set."
        )
        self.assertIn(
            user.name,
            facility.display_modified_info,
            "Modification info should include the user name.",
        )

    #
    def test_rec_status_computation(self):
        """
        Test rec_status computation to ensure it correctly reflects the active status.
        """
        facility = self.env["container.facilities"].create(
            {
                "name": "Test Facility Status",
                "facility_type": "cfs",
                "code": "STATUS_TEST",
                "port": self.port.id,
                "company_id": self.test_company.id,
            }
        )

        # By default, active is True, so rec_status should be 'active'
        facility._check_active_records()  # Trigger the status check
        self.assertEqual(
            facility.rec_status,
            "active",
            "The status should be 'active' when the record is active.",
        )

        # Change active to False and check the status again
        facility.write({"active": False})
        facility._check_active_records()  # Trigger the status check
        self.assertEqual(
            facility.rec_status,
            "disable",
            "The status should be 'disable' when the record is inactive.",
        )
