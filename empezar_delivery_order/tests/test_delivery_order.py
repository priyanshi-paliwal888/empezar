from datetime import datetime, timedelta
import pytz
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestDeliveryOrder(TransactionCase):

    def setUp(self):
        super().setUp()
        # Create a user without a timezone
        self.user_no_tz = self.env["res.users"].create(
            {
                "name": "Test User No tz",
                "login": "test_user_no_tz",
            }
        )

        # Load or create necessary records
        self.shipping_line = self.env["res.partner"].create(
            {"name": "Test Shipping Line", "is_shipping_line": True, "active": True}
        )
        self.exporter = self.env["res.partner"].create(
            {
                "name": "Test Exporter",
                "parties_type_ids": [
                    (6, 0, [self.env.ref("empezar_base.cms_parties_type_1").id])
                ],
            }
        )
        self.booking_party = self.env["res.partner"].create(
            {
                "name": "Test Booking Party",
                "parties_type_ids": [
                    (6, 0, [self.env.ref("empezar_base.cms_parties_type_2").id])
                ],
            }
        )
        self.forwarder = self.env["res.partner"].create(
            {
                "name": "Test Forwarder",
                "parties_type_ids": [
                    (6, 0, [self.env.ref("empezar_base.cms_parties_type_3").id])
                ],
            }
        )
        self.importer = self.env["res.partner"].create(
            {
                "name": "Test Importer",
                "parties_type_ids": [
                    (6, 0, [self.env.ref("empezar_base.cms_parties_type_4").id])
                ],
            }
        )
        self.to_from_location = self.env["res.company"].create(
            {"name": "Test To/From Location"}
        )
        self.stuffing_location = self.env["res.company"].create(
            {"name": "Test Stuffing Location"}
        )
        self.test_company = self.env["res.company"].create(
            {"name": "Test Terminal", "location_type": "terminal"}
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
                "container_yard":facility.id,
            }
        )

        self.facility = self.env["container.facilities"].create(
            {
                "name": "Test Facility Modify Info",
                "facility_type": "empty_yard",
                "code": "MODIFY_INFO",
                "port": self.port_loading.id,
                "company_id": self.test_company.id,
            }
        )

        self.delivery_order = self.env["delivery.order"].create(
            {
                "delivery_no": "DO123",
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

    def test_create_delivery_order(self):
        """Test creating a Delivery Order"""
        delivery_order = self.env["delivery.order"].create(
            {
                "delivery_no": "DO001",
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

        self.assertEqual(delivery_order.delivery_no, "DO001")
        self.assertEqual(delivery_order.shipping_line_id, self.shipping_line)
        self.assertEqual(delivery_order.total_containers, 10)

    def test_check_unique_delivery_no_shipping_line(self):
        """Test constraint for unique delivery_no and shipping_line_id"""
        self.env["delivery.order"].create(
            {
                "delivery_no": "DO002",
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

        with self.assertRaises(ValidationError):
            self.env["delivery.order"].create(
                {
                    "delivery_no": "DO002",
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

    def test_cargo_weight_numeric_validation(self):
        """Test cargo weight numeric validation"""
        with self.assertRaises(ValidationError):
            self.env["delivery.order"].create(
                {
                    "delivery_no": "DO003",
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
                    "cargo_weight": "1000kg",  # Invalid
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

    def test_compute_check_active_records(self):
        """Test the computed field for active records"""
        delivery_order = self.env["delivery.order"].create(
            {
                "delivery_no": "DO004",
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

        delivery_order.active = False
        delivery_order._compute_check_active_records()
        self.assertEqual(delivery_order.rec_status, "disable")

        delivery_order.active = True
        delivery_order._compute_check_active_records()
        self.assertEqual(delivery_order.rec_status, "active")

    def test_update_allocations(self):
        """Test view allocations action"""
        view_id = self.env.ref(
            "empezar_delivery_order.update_allocation_wizard_form_view"
        ).id
        container_details_ids = self.delivery_order.container_details.ids
        action = self.delivery_order.update_allocations()
        self.assertEqual(action["name"], "Update Allocations")
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["view_mode"], "form")
        self.assertEqual(action["view_id"], view_id)
        self.assertEqual(action["res_model"], "view.update.allocation.wizard")
        self.assertEqual(
            action["context"]["default_delivery_order_id"], self.delivery_order.id
        )
        self.assertEqual(
            action["context"]["default_container_details"],
            [(6, 0, container_details_ids)],
        )

    def test_view_allocations(self):
        """Test view allocations action"""
        action = self.delivery_order.view_allocations()

    def test_compute_display_name(self):
        """Test display name computation"""
        self.delivery_order._compute_display_name()
        self.assertIn('DO123',self.delivery_order.display_name)

    def test_check_container_types_present(self):
        """Test that at least one container detail is selected"""
        with self.assertRaises(ValidationError):
            self.env["delivery.order"].create(
                {
                    "delivery_no": "DO126",
                    "shipping_line_id": self.shipping_line.id,
                    "terminal": self.facility.id,
                    "delivery_date": datetime.now().date(),
                    "validity_datetime": datetime.now() + timedelta(days=1),
                    "exporter_name": self.exporter.id,
                    "booking_party": self.booking_party.id,
                    "forwarder_name": self.forwarder.id,
                    "import_name": self.importer.id,
                    "commodity": "Test Commodity",
                    "cargo_weight": "1000",
                    "vessel": "Test Vessel",
                    "voyage": "Test Voyage",
                    "remark": "Test Remark",
                    "port_loading": self.port_loading.id,
                    "port_discharge": self.port_discharge.id,
                    "location": [(6, 0, [self.location.id])],
                    "to_from_location": self.to_from_location.id,
                    "stuffing_location": self.stuffing_location.id,
                    "container_details": [(6, 0, [])],
                }
            )

    def test_check_delivery_date(self):
        """Test that the delivery date is not in the future"""
        future_date = datetime.now().date() + timedelta(days=1)
        with self.assertRaises(ValidationError):
            self.env["delivery.order"].create(
                {
                    "delivery_no": "DO127",
                    "shipping_line_id": self.shipping_line.id,
                    "terminal": self.facility.id,
                    "delivery_date": future_date,
                    "validity_datetime": datetime.now() + timedelta(days=1),
                    "exporter_name": self.exporter.id,
                    "booking_party": self.booking_party.id,
                    "forwarder_name": self.forwarder.id,
                    "import_name": self.importer.id,
                    "commodity": "Test Commodity",
                    "cargo_weight": "1000",
                    "vessel": "Test Vessel",
                    "voyage": "Test Voyage",
                    "remark": "Test Remark",
                    "port_loading": self.port_loading.id,
                    "port_discharge": self.port_discharge.id,
                    "location": [(6, 0, [self.location.id])],
                    "to_from_location": self.to_from_location.id,
                    "stuffing_location": self.stuffing_location.id,
                }
            )

    def test_check_validity_datetime(self):
        """Test that the validity datetime is not before the delivery date"""
        past_date = datetime.now() - timedelta(days=1)
        with self.assertRaises(ValidationError):
            self.env["delivery.order"].create(
                {
                    "delivery_no": "DO128",
                    "shipping_line_id": self.shipping_line.id,
                    "terminal": self.facility.id,
                    "delivery_date": datetime.now().date(),
                    "validity_datetime": past_date,
                    "exporter_name": self.exporter.id,
                    "booking_party": self.booking_party.id,
                    "forwarder_name": self.forwarder.id,
                    "import_name": self.importer.id,
                    "commodity": "Test Commodity",
                    "cargo_weight": "1000",
                    "vessel": "Test Vessel",
                    "voyage": "Test Voyage",
                    "remark": "Test Remark",
                    "port_loading": self.port_loading.id,
                    "port_discharge": self.port_discharge.id,
                    "location": [(6, 0, [self.location.id])],
                    "to_from_location": self.to_from_location.id,
                    "stuffing_location": self.stuffing_location.id,
                }
            )

    def test_compute_get_create_record_info(self):
        """Test computation of create record information"""
        self.delivery_order._compute_get_create_record_info()
        self.assertTrue(self.delivery_order.display_create_info)
        # Set the current user for the environment to simulate the context
        self.env = self.env(user=self.user_no_tz)
        delivery_order = self.env["delivery.order"].create(
            {
                "delivery_no": "DO006",
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
        delivery_order.create_uid = self.user_no_tz.id
        delivery_order._compute_get_create_record_info()

        # Assert the display_modified_info is empty
        self.assertEqual(delivery_order.display_modified_info, "")

    def test_compute_get_modify_record_info(self):
        """Test computation of modify record information"""
        self.delivery_order.write({"commodity": "Updated Commodity"})
        self.delivery_order._compute_get_modify_record_info()
        self.assertTrue(self.delivery_order.display_modified_info)
        # Set the current user for the environment to simulate the context
        self.env = self.env(user=self.user_no_tz)
        delivery_order = self.env["delivery.order"].create(
            {
                "delivery_no": "DO007",
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
        delivery_order.write_uid = self.user_no_tz.id
        delivery_order._compute_get_modify_record_info()

        # Assert the display_modified_info is empty
        self.assertEqual(delivery_order.display_modified_info, "")
