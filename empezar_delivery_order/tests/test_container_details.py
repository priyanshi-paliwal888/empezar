from datetime import datetime, timedelta
from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError


class TestContainerDetails(TransactionCase):

    def setUp(self):
        super().setUp()

        # Create test data
        self.delivery_order_model = self.env["delivery.order"]
        self.container_details_model = self.env["container.details.delivery"]
        self.res_company_model = self.env["res.company"]
        self.container_type_model = self.env["container.type.data"]

        self.company = self.res_company_model.create(
            {"name": "Test Company", "location_type": "empty_yard"}
        )
        self.container_type = self.container_type_model.create(
            {"name": "20ft", "is_refer": "yes"}
        )
        self.container_type_02 = self.container_type_model.create(
            {"name": "200ft", "is_refer": "yes"}
        )
        # Load or create necessary records
        self.shipping_line = self.env["res.partner"].create(
            {"name": "Test Shipping Line", "is_shipping_line": True, "active": True}
        )
        self.master_port_data_model = self.env["master.port.data"]
        # Create a port for loading
        self.port_loading = self.master_port_data_model.create(
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
        # Create a port for discharge
        self.port_discharge = self.master_port_data_model.create(
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
        self.location = self.env["res.company"].create(
            {"name": "Test Location", "active": True}
        )

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

        facility_data = {
            "name": "Test Facility",
            "facility_type": "empty_yard",
            "code": "TF001",
            "port": self.port.id,
            "active": True,
        }
        facility = self.env['container.facilities'].create(facility_data)

        self.container_details = self.env["container.details.delivery"].create(
            {
                "delivery_id": False,  # Will be set after creating the delivery order
                "container_qty": 10,
                "balance_container": 5,
                "container_size_type": self.env["container.type.data"].create({"name": "20ft", "is_refer": "yes"}).id,
                "container_yard": facility.id,
            }
        )
        self.delivery_order = self.env["delivery.order"].create(
            {
                "delivery_no": "DO151",
                "shipping_line_id": self.shipping_line.id,
                "delivery_date": datetime.today().date(),
                "validity_datetime": datetime.today() + timedelta(days=1),
                "exporter_name": self.env["res.partner"]
                .create({"name": "Test Exporter"})
                .id,
                "booking_party": self.env["res.partner"]
                .create({"name": "Test Booking Party"})
                .id,
                "forwarder_name": self.env["res.partner"]
                .create({"name": "Test Forwarder"})
                .id,
                "import_name": self.env["res.partner"]
                .create({"name": "Test Importer"})
                .id,
                "commodity": "Test Commodity",
                "cargo_weight": "1000",
                "vessel": "Test Vessel",
                "voyage": "Test Voyage",
                "remark": "Test Remark",
                "port_loading": self.port_loading.id,
                "port_discharge": self.port_discharge.id,
                "location": [(6, 0, [self.location.id])],
                "to_from_location": self.location.id,
                "stuffing_location": self.location.id,
                "total_containers": 10,
                "balance_containers": 5,
                "container_details": [(6, 0, [self.container_details.id])],
            }
        )
        self.delivery_order_02 = self.env["delivery.order"].create(
            {
                "delivery_no": "DO152",
                "shipping_line_id": self.shipping_line.id,
                "delivery_date": datetime.today().date(),
                "validity_datetime": datetime.today() + timedelta(days=1),
                "exporter_name": self.env["res.partner"]
                .create({"name": "Test Exporter"})
                .id,
                "booking_party": self.env["res.partner"]
                .create({"name": "Test Booking Party"})
                .id,
                "forwarder_name": self.env["res.partner"]
                .create({"name": "Test Forwarder"})
                .id,
                "import_name": self.env["res.partner"]
                .create({"name": "Test Importer"})
                .id,
                "commodity": "Test Commodity",
                "cargo_weight": "1000",
                "vessel": "Test Vessel",
                "voyage": "Test Voyage",
                "remark": "Test Remark",
                "port_loading": self.port_loading.id,
                "port_discharge": self.port_discharge.id,
                "location": [(6, 0, [self.location.id])],
                "to_from_location": self.location.id,
                "stuffing_location": self.location.id,
                "total_containers": 10,
                "balance_containers": 5,
                "container_details": [(6, 0, [self.container_details.id])],
            }
        )

    def test_check_unique_container_type(self):
        """Test the _check_unique_container_type constraint."""

        # Create a ContainerDetails record
        self.container_details_model.create(
            {
                "delivery_id": self.delivery_order.id,
                "container_qty": 10,
                "container_size_type": self.container_type.id,
            }
        )

        # Try to create a duplicate ContainerDetails record with the same container_size_type for the same delivery_id
        with self.assertRaises(ValidationError):
            self.container_details_model.create(
                {
                    "delivery_id": self.delivery_order.id,
                    "container_qty": 20,
                    "container_size_type": self.container_type.id,
                }
            )

    def test_check_container_qty(self):
        """Test the _check_container_qty constraint."""

        # Create a ContainerDetails record with valid container_qty
        self.container_details_model.create(
            {
                "delivery_id": self.delivery_order.id,
                "container_qty": 100,
                "container_size_type": self.container_type.id,
            }
        )

        # Try to create a ContainerDetails record with invalid container_qty (less than 1)
        with self.assertRaises(ValidationError):
            self.container_details_model.create(
                {
                    "delivery_id": self.delivery_order_02.id,
                    "container_qty": 0,
                    "container_size_type": self.container_type.id,
                }
            )

        # Try to create a ContainerDetails record with invalid container_qty (greater than 999)
        with self.assertRaises(ValidationError):
            self.container_details_model.create(
                {
                    "delivery_id": self.delivery_order.id,
                    "container_qty": 1000,
                    "container_size_type": self.container_type.id,
                }
            )

    # def test_compute_total_containers(self):
    #     """Test the _compute_total_containers method."""
    #
    #     # Create ContainerDetails records
    #     container_details_01 = self.container_details_model.create({
    #         'delivery_id': self.delivery_order.id,
    #         'container_qty': 10,
    #         'container_size_type': self.container_type.id,
    #     })
    #     container_details_02 = self.container_details_model.create({
    #         'delivery_id': self.delivery_order.id,
    #         'container_qty': 20,
    #         'container_size_type': self.container_type_02.id,
    #     })
    #
    #     # Trigger the compute method
    #     container_details_02._compute_total_containers()
    #
    #     # Check the total_containers value
    #     self.assertEqual(self.delivery_order.total_containers, 30)

    # def test_compute_balance_total_containers(self):
    #     """Test the _compute_balance_total_containers method."""
    #
    #     # Create ContainerDetails records with balance_container values
    #     container_details_01 = self.container_details_model.create({
    #         'delivery_id': self.delivery_order.id,
    #         'balance_container': 5,
    #         'container_qty':111,
    #         'container_size_type': self.container_type.id,
    #     })
    #     container_details_02 = self.container_details_model.create({
    #         'delivery_id': self.delivery_order.id,
    #         'balance_container': 15,
    #         'container_qty':112,
    #         'container_size_type': self.container_type_02.id,
    #     })
    #
    #     # Trigger the compute method
    #     container_details_02._compute_balance_total_containers()
    #
    #     # Check the balance_containers value
    #     self.assertEqual(self.delivery_order.balance_containers, 20)
