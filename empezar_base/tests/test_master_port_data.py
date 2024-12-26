from odoo.tests.common import TransactionCase


class TestMasterPortData(TransactionCase):

    def setUp(self):
        super().setUp()
        self.port_data_model = self.env["master.port.data"]

    def test_compute_display_name(self):
        # Create a new port data record
        port_data = self.port_data_model.create(
            {
                "port_name": "Los Angeles Port",
                "port_code": "LAX",
                "country_iso_code": "US",
                "state_code": "CA",
                "status": "Active",
                "latitude": "34.0522",
                "longitude": "-118.2437",
                "popular_port": True,
                "active": True,
            }
        )

        # Check if the display_name is computed correctly
        expected_display_name = "Los Angeles Port(USLAX)"
        self.assertEqual(port_data.display_name, expected_display_name)

        # Create another port data record with different values
        port_data2 = self.port_data_model.create(
            {
                "port_name": "New York Port",
                "port_code": "NYC",
                "country_iso_code": "US",
                "state_code": "NY",
                "status": "Active",
                "latitude": "40.7128",
                "longitude": "-74.0060",
                "popular_port": True,
                "active": True,
            }
        )

        # Check if the display_name is computed correctly
        expected_display_name2 = "New York Port(USNYC)"
        self.assertEqual(port_data2.display_name, expected_display_name2)
