from odoo.tests.common import TransactionCase
from odoo import fields
from datetime import datetime, timedelta

class TestContainerNumber(TransactionCase):

    def setUp(self):
        super(TestContainerNumber, self).setUp()

        self.partner_shipping_line = self.env['res.partner'].create({
            'name': 'Shipping Line',
            'is_shipping_line': True,
        })
        self.partner_transporter = self.env['res.partner'].create({
            'name': 'Transporter',
            'parties_type_ids': [(0, 0, {'name': 'Transporter'})],
        })
        self.location = self.env['res.company'].create({'name': 'Location'})
        self.container_type = self.env['container.type.data'].create({
            'name': '20 FT',
            'company_size_type_code': '20FT',
            'is_refer': 'no',
            'active': True,
            'company_id': self.env.company.id
        })
        self.container_detail = self.env['container.details'].create({
            'container_size_type': self.container_type.id,
            'container_qty': 10,
            'balance': 5,
        })
        self.container_number1 = self.env['container.number'].create({
            'name': 'GVTU3000389',
            'unlink_reason': False,
            'is_unlink': False,
            'is_unlink_non_editable': False
        })
        self.booking = self.env['vessel.booking'].create({
            'shipping_line_id': self.partner_shipping_line.id,
            'transporter_name': self.partner_transporter.id,
            'location': [(6, 0, [self.location.id])],
            'booking_no': 'BOOK001',
            'booking_date': fields.Date.today(),
            'validity_datetime': fields.Datetime.now(),
            'cutoff_datetime': fields.Datetime.now(),
            'vessel': 'Test Vessel',
            'voyage': '12345',
            'container_details': [(6, 0, [self.container_detail.id])],
            'container_numbers': [(6, 0, [self.container_number1.id])]
        })

        self.container_type = self.env["container.type.data"].create(
            {
                "name": "20 FT",
                "company_size_type_code": "20FT",
                "is_refer": "no",
                "active": True,
                "company_id": self.location.id,
            }
        )

        # Create Container Detail
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

        self.container_delivery_detail = self.env["container.details.delivery"].create(
            {
                "container_qty": 10,
                "balance_container": 5,
                "quantity": 5,
                "container_size_type": self.container_type.id,
                "container_yard": facility.id,
            }
        )

        self.shipping_line = self.env["res.partner"].create(
            {
                "name": "Test Shipping Line",
                "company_id": self.location.id,
            }
        )

        self.delivery_order = self.env["delivery.order"].create(
            {
                "delivery_no": "DO1234",
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
                # "port_loading": self.port_loading.id,
                # "port_discharge": self.port_discharge.id,
                "location": [(6, 0, [self.location.id])],
                "to_from_location": self.location.id,
                "stuffing_location": self.location.id,
                "total_containers": 10,
                "balance_containers": 5,
                "container_details": [(6, 0, [self.container_delivery_detail.id])],
            }
        )

        self.container_master = self.env["container.master"].create(
            {
                "name": "GVTU3000389",
                "type_size": self.container_type.id,
                "shipping_line_id": self.shipping_line.id,
                "gross_wt": "123",
                "tare_wt": "123",
            }
        )

        self.container_inventory = self.env["container.inventory"].create(
            {
                "name": "GVTU3000389",
                "grade": "a",
                "location_id": self.location.id,
                "container_master_id": self.container_master.id,
            }
        )

        self.damage_condition = self.env["damage.condition"].create(
            {"name": "Damage A", "damage_code": "Size/Type A", "active": True}
        )

        self.move_in = self.env["move.in"].create(
            {
                "container": "GVTU3000389",
                "location_id": self.location.id,
                "do_no_id": self.delivery_order.id,
                "mode": "truck",
                "damage_condition": self.damage_condition.id,
                "shipping_line_id": self.shipping_line.id,
                "type_size_id": self.container_type.id,
                "grade": "a",
                "gross_wt": 10,
                "tare_wt": 5
            }
        )

        self.move_out = self.env['move.out'].create({
            'shipping_line_id': self.shipping_line.id,
            'inventory_id': self.container_inventory.id,
            'location_id': self.location.id,
            'delivery_order_id': self.delivery_order.id,
            'move_out_date_time': fields.Datetime.now(),
            'movement_type': 'export_stuffing',
            'export_stuffing_to': 'factory',
            'mode': 'truck',
            'truck_number': 'TRK1234',
            'driver_name': 'John Doe',
            'driver_mobile_number': '1234567890',
            'driver_licence_no': 'LIC123456',
            'container_id': self.container_number1.id,
        })

    def test_compute_update_container_dates(self):
        """Test that move in/out date times are updated correctly."""
        self.container_number1.compute_update_container_dates()
        self.assertEqual(self.container_number1.move_in_datetime, self.move_in.move_in_date_time)
        self.assertEqual(self.container_number1.move_out_datetime, self.move_out.move_out_date_time)