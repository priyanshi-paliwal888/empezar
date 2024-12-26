from datetime import datetime, timedelta
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from odoo import fields

class TestMoveIn(TransactionCase):

    def setUp(self):
        super().setUp()

        # Setup code as provided
        self.mode = self.env["mode.options"].create({"name": "mode"})
        self.truck_mode = self.env["mode.options"].create({"name": "Truck"})
        self.rail_mode = self.env["mode.options"].create({"name": "Rail"})
        self.gate_pass = self.env["gate.pass.options"].create({"name": "Move In"})

        self.shipping_line = self.env["res.partner"].create(
            {
                "name": "Test Shipping Line",
                "company_id": self.env.company.id,
            }
        )

        self.location = self.env["res.company"].create(
            {
                "name": "Test Location",
                "active": True,
            }
        )
        self.location_2 = self.env["res.company"].create(
            {
                "name": "Test Location 2",
                "active": True,
            }
        )

        self.container_type_size = self.env["container.type.data"].create(
            {
                "name": "20FT",
                "company_size_type_code": "20FT",
                "is_refer": "no",
            }
        )

        self.damage_condition = self.env["damage.condition"].create(
            {"name": "Damage A", "damage_code": "Size/Type A", "active": True}
        )

        self.type_size = self.env['container.type.data'].create({
            'name': '20 FT',
            'company_size_type_code': '20FT',
            'is_refer': 'no',
            'active': True,
            'company_id': self.location.id
        })

        self.container_master = self.env['container.master'].create({
            'name': 'GVTU3000389',
            'type_size': self.type_size.id
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

        self.container_detail = self.env["container.details"].create(
            {
                "container_size_type": self.container_type.id,
                "container_qty": 10,
                "balance": 5,
            }
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

        self.container_delivery_detail = self.env["container.details.delivery"].create(
            {
                "container_qty": 10,
                "balance_container": 5,
                "quantity": 5,
                "container_size_type": self.container_type.id,
                "container_yard": facility.id,
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
                "location": [(6, 0, [self.location.id])],
                "to_from_location": self.location.id,
                "stuffing_location": self.location.id,
                "total_containers": 10,
                "balance_containers": 5,
                "container_details": [(6, 0, [self.container_delivery_detail.id])],
            }
        )

        self.partner_transporter = self.env["res.partner"].create(
            {
                "name": "Transporter",
                "parties_type_ids": [(0, 0, {"name": "Transporter"})],
            }
        )


        self.booking = self.env["vessel.booking"].create(
            {
                "shipping_line_id": self.shipping_line.id,
                "transporter_name": self.partner_transporter.id,
                "location": [(6, 0, [self.location.id])],
                "booking_no": "BOOK001",
                "booking_date": fields.Date.today(),
                "validity_datetime": fields.Datetime.now(),
                "cutoff_datetime": fields.Datetime.now(),
                "vessel": "Test Vessel",
                "voyage": "12345",
                "container_details": [(6, 0, [self.container_detail.id])],
            }
        )

        self.container_number1 = self.env['container.number'].create({
            'name': 'GVTU3000389',
            'unlink_reason': False,
            'is_unlink': False,
            'is_unlink_non_editable': False
        })

        self.move_in = self.env["move.in"].create(
            {
                "container": "GVTU3000389",
                "location_id": self.location.id,
                "do_no_id": self.delivery_order.id,
                "mode": "truck",
                "damage_condition": self.damage_condition.id,
                "shipping_line_id": self.shipping_line.id,
                "type_size_id": self.container_type_size.id,
                "grade": "a",
                "gross_wt": 10,
                "tare_wt":5
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

    def test_move_in_creation(self):
        """Test creation of Move In record."""
        self.assertEqual(self.move_in.container, "GVTU3000389")
        self.assertEqual(self.move_in.location_id, self.location)
        self.assertEqual(self.move_in.mode, "truck")
        self.assertEqual(self.move_in.damage_condition, self.damage_condition)
        self.assertEqual(self.move_in.shipping_line_id, self.shipping_line)
        self.assertEqual(self.move_in.type_size_id, self.container_type_size)
        self.assertEqual(self.move_in.grade, "a")

    def test_unique_container_constraint(self):
        """Test that the same container cannot be added twice."""
        with self.assertRaises(ValidationError):
            self.env["move.in"].create(
                {
                    "container": "GVTU3000389",  # Duplicate container
                    "location_id": self.location.id,
                    "mode": "truck",
                    "damage_condition": self.damage_condition.id,
                    "shipping_line_id": self.shipping_line.id,
                    "type_size_id": self.container_type_size.id,
                    "grade": "a",
                    "gross_wt": 10,
                    "tare_wt": 5
                }
            )

    def test_mode_options(self):
        """Test that mode options are validated correctly."""
        valid_modes = ["truck", "rail"]  # Assuming these are valid modes
        container = ["FUJU1234568", "EUJU1234567"]  # Assuming these are valid modes
        for mode,container_no in zip(valid_modes,container):
            move_in = self.env["move.in"].create(
                {
                    "container": container_no,
                    "location_id": self.location_2.id,
                    "mode": mode,
                    "damage_condition": self.damage_condition.id,
                    "shipping_line_id": self.shipping_line.id,
                    "type_size_id": self.container_type_size.id,
                    "grade": "a",
                    "gross_wt": 10,
                    "tare_wt": 5
                }
            )
            self.assertEqual(move_in.mode, mode)

    def test_damage_condition_association(self):
        """Test that a Move In record correctly associates with a damage condition."""
        move_in = self.env["move.in"].create(
            {
                "container": "EUJU1234567",
                "location_id": self.location_2.id,
                "mode": "truck",
                "damage_condition": self.damage_condition.id,
                "shipping_line_id": self.shipping_line.id,
                "type_size_id": self.container_type_size.id,
                "grade": "a",
                "gross_wt": 10,
                "tare_wt": 5
            }
        )
        self.assertEqual(move_in.damage_condition, self.damage_condition)

    def test_on_change_movement_type(self):
        """Test that fields are cleared correctly based on the selected movement type."""
        self.move_in.movement_type = False
        self.move_in.onchange_movement_type()
        self.assertFalse(self.move_in.import_destuffing_from)

        self.move_in.movement_type = 'import_destuffing'
        self.move_in.onchange_movement_type()
        self.assertFalse(self.move_in.from_port)
        self.assertFalse(self.move_in.from_terminal)
        self.assertFalse(self.move_in.from_cfs_icd)

        self.move_in.movement_type = 'repo'
        self.move_in.onchange_movement_type()

        # Check that relevant fields are cleared
        self.assertFalse(self.move_in.import_destuffing_from)
        self.assertFalse(self.move_in.from_cfs_icd)

    def test_invalid_container_not_in_master(self):
        """Test an invalid container number not in the master data."""
        with self.assertRaises(ValidationError):
            self.move_in.container = "INVALID_CONTAINER"
            self.move_in.check_container_number_validations()

    def test_location_required_validation(self):
        """Test that location_id is required for validations."""
        self.move_in.location_id = False
        self.move_in.container = "GVTU3000389"
        self.move_in.check_container_number_validations()
        # self.assertEqual(self.move_in.grade, False)
        # self.assertEqual(self.move_in.damage_condition, False)

    def test_container_number_uppercase(self):
        """Test that the container number is set to uppercase."""
        with self.assertRaises(ValidationError):
            self.move_in.container = "gvtU3000389"
            self.move_in.check_container_number_validations()

    def test_compute_delivery_domain(self):
        """ Test delivery domain computation based on location and move in records. """
        self.move_in.movement_type = 'import_destuffing'
        self.move_in._compute_do_no_domain()
        self.assertEqual(self.delivery_order.id, self.move_in.do_no_compute_domain.id,"Delivery domain should include the valid delivery order.")


    def test_compute_booking_domain(self):
        """ Test booking domain computation based on location and move in records. """
        self.move_in._compute_booking_no_domain()
        self.assertEqual(self.booking.id, self.move_in.booking_no_compute_domain.id,"Booking domain should include the valid booking.")

    def test_populate_seal_numbers(self):
        """Test that seal numbers are populated correctly based on the movement type and container."""

        seal_1 = self.env["seal.management"].create(
            {
                "seal_number": 'SEAL123',
                "shipping_line_id": self.shipping_line.id,
                "location": self.location.id,
            }
        )

        seal_2 = self.env["seal.management"].create(
            {
                "seal_number": 'SEAL456',
                "shipping_line_id": self.shipping_line.id,
                "location": self.location.id,
            }
        )
        self.env['move.out'].create({
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
            'seal_no_1':seal_1.id,
            'seal_no_2':seal_2.id
        })

        self.move_in.movement_type = 'factory_return'
        self.move_in.populate_seal_numbers()

        # Check that the seal numbers are populated correctly
        self.assertEqual(self.move_in.seal_no_1, "SEAL123", "Seal No 1 should be populated from the latest move out.")
        self.assertEqual(self.move_in.seal_no_2, "SEAL456", "Seal No 2 should be populated from the latest move out.")

    def test_get_edit_popup_message(self):
        # Set up the necessary conditions for the test
        self.move_in.is_edi_send = True
        self.move_in.is_damage_edi_send = True
        self.move_in.gate_pass_no = "GP123"