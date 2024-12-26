from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
from odoo import fields


class TestDeliveryOrderModel(TransactionCase):

    def setUp(self):
        super(TestDeliveryOrderModel, self).setUp()
        # Load or create necessary records
        self.shipping_line = self.env["res.partner"].create(
            {"name": "Test Shipping Line", "is_shipping_line": True, "active": True}
        )
        self.master_port_data_model = self.env["master.port.data"]
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
                "delivery_id": False,
                "container_qty": 10,
                "balance_container": 5,
                "container_size_type": self.env["container.type.data"]
                .create({"name": "20ft", "is_refer": "yes"})
                .id,
                "container_yard": facility.id,
            }
        )

        self.facility = self.env["container.facilities"].create(
            {
                "name": "Test Facility Modify Info",
                "facility_type": "empty_yard",
                "code": "MODIFY_INFO",
                "port": self.port_loading.id,
                "company_id": self.location.id,
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

        self.container_type_size = self.env["container.type.data"].create(
            {
                "name": "20FT",
                "company_size_type_code": "20FT",
                "is_refer": "yes",
            }
        )

        self.container_master = self.env["container.master"].create(
            {
                "name": "GVTU3000389",
                "type_size": self.container_type_size.id,
                "shipping_line_id": self.shipping_line.id,
                "gross_wt": "123",
                "tare_wt": "123",
            }
        )

        self.container_inventory = self.env['container.inventory'].create({
            'container_master_id': self.container_master.id,
            'location_id': self.location.id,
            'name': 'GVTU3000389',
        })

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
                "type_size_id": self.container_type_size.id,
                "grade": "a",
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
            'driver_licence_no': 'LIC123456'
        })

    def test_default_get_is_from_move_out(self):
        """Test the default_get method when the context is set with 'is_from_move_out' and 'is_from_delivery_order'."""
        context = {
            'is_from_move_out': True,
            'is_from_delivery_order': True,
            'default_name': 'DO001',
            'location_id': self.location.id,
        }

        delivery_order = self.env['delivery.order'].with_context(**context).default_get(['delivery_no', 'location'])
        self.assertEqual(delivery_order['delivery_no'], 'DO001')
        self.assertIn(self.location.id, delivery_order['location'][0][2])

    def test_check_delivery_active_constraint_move_out(self):
        """Test the constraint where a record can't be archived if it exists in Move Out."""
        # Try archiving a delivery order with an associated active move_out record
        with self.assertRaises(ValidationError):
            self.delivery_order.write({'active': False})

    def test_check_delivery_active_constraint_move_in(self):
        """Test the constraint where a record can't be archived if it exists in Move In."""
        self.move_out.unlink()
        with self.assertRaises(ValidationError):
            self.delivery_order.write({'active': False})

    def test_compute_is_delivery_in_move_out(self):
        """Test the _compute_delivery_order_in_move_out compute method."""
        self.delivery_order._compute_delivery_order_in_move_out()
        self.assertTrue(self.delivery_order.is_delivery_in_move_out)

        self.move_out.unlink()
        self.delivery_order._compute_delivery_order_in_move_out()
        self.assertFalse(self.delivery_order.is_delivery_in_move_out)

    def test_view_allocations(self):
        # Ensure the method executes without errors
        wizard_action = self.delivery_order.view_allocations()
        self.assertTrue(wizard_action, "The view_allocations method did not return an action.")

        # Verify the returned action's details
        self.assertEqual(
            wizard_action['res_model'],
            'view.update.allocation.wizard',
            "The action does not point to the correct wizard model."
        )
        self.assertEqual(
            wizard_action['view_mode'],
            'form',
            "The action view mode is not 'form'."
        )

        # Validate the created allocation history lines
        history_lines = self.env['view.allocation.history.line.wizard'].search([
            ('delivery_id', '=', self.delivery_order.id)
        ])
        self.assertGreater(len(history_lines), 0, "No allocation history lines were created.")

        # Check the context of the returned action
        self.assertIn('default_delivery_order_id', wizard_action['context'], "Delivery order ID is not in the context.")
        self.assertEqual(
            wizard_action['context']['default_delivery_order_id'],
            self.delivery_order.id,
            "Delivery order ID in context does not match the current delivery order."
        )
        self.assertIn('default_history_line_ids', wizard_action['context'], "History lines are not in the context.")
        self.assertEqual(
            len(wizard_action['context']['default_history_line_ids'][0][2]),
            len(history_lines),
            "Mismatch in number of history lines between context and created records."
        )
