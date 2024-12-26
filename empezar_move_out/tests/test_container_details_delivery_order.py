# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError
from odoo import fields, _


class TestContainerDetails(TransactionCase):

    def setUp(self):
        super().setUp()

        # Create test data
        self.delivery_order_model = self.env["delivery.order"]
        self.container_details_model = self.env["container.details.delivery"]
        self.res_company_model = self.env["res.company"]
        self.container_type_model = self.env["container.type.data"]
        self.location = self.env["res.company"].create(
            {"name": "Test Location", "active": True}
        )
        self.company = self.res_company_model.create(
            {"name": "Test Company", "location_type": "empty_yard"}
        )
        self.container_type = self.container_type_model.create(
            {"name": "20ft", "is_refer": "yes"}
        )
        self.container_type_02 = self.container_type_model.create(
            {"name": "200ft", "is_refer": "yes"}
        )
        self.shipping_line = self.env["res.partner"].create(
            {"name": "Test Shipping Line", "is_shipping_line": True, "active": True}
        )

        # Create ports
        self.port_loading = self.env["master.port.data"].create({
            "country_iso_code": "US",
            "port_code": "TESTPORT",
            "port_name": "Test Port",
            "state_code": "NY",
            "status": "Active",
            "latitude": "40.7128° N",
            "longitude": "74.0060° W",
            "popular_port": True,
            "active": True,
        })

        self.port_discharge = self.env["master.port.data"].create({
            "country_iso_code": "US",
            "port_code": "TESTPORT",
            "port_name": "Test Port",
            "state_code": "NY",
            "status": "Active",
            "latitude": "40.7128° N",
            "longitude": "74.0060° W",
            "popular_port": True,
            "active": True,
        })

        facility_data = {
            "name": "Test Facility",
            "facility_type": "empty_yard",
            "code": "TF001",
            "port": self.port_discharge.id,
            "active": True,
        }
        facility = self.env['container.facilities'].create(facility_data)

        self.container_details = self.container_details_model.create(
            {
                "delivery_id": False,  # Will be set after creating the delivery order
                "container_qty": 10,
                "balance_container": 5,
                "container_size_type": self.container_type.id,
                "container_yard": facility.id,
            }
        )

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

        self.container_type_size = self.env["container.type.data"].create(
            {
                "name": "20FT",
                "company_size_type_code": "20FT",
                "is_refer": "yes",
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

        self.facility = self.env["container.facilities"].create(
            {
                "name": "Test Facility Modify Info",
                "facility_type": "empty_yard",
                "code": "MODIFY_INFO",
                "port": self.port_loading.id,
                "company_id": self.location.id,
            }
        )

        self.container_details = self.env["container.details.delivery"].create(
            {
                "delivery_id": False,  # Will be set after creating the delivery order
                "container_qty": 10,
                "balance_container": 5,
                "container_size_type": self.container_type_size.id,
                "container_yard": self.facility.id,
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
        #
        self.move_in = self.env["move.in"].create(
            {
                "container": "GVTU3000389",
                "location_id": self.location.id,
                "do_no_id": self.delivery_order.id,
                # "booking_no_id": self.booking.id,
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

    def test_count_computation(self):
        """ Test the computation of count based on related move.out and move.in records. """
        self.container_details._compute_count()
        self.assertGreater(self.container_details.count, 0)

    def test_view_records_action(self):
        """ Test the action that opens the allocation wizard with the correct context. """
        action = self.container_details.view_records()

        # Verify the action dictionary
        self.assertEqual(action['name'], _('View Allocations'))
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'view.update.allocation.wizard')

        # Check context values
        context = action['context']
        self.assertEqual(context['default_delivery_order_id'], self.container_details.delivery_id)
        self.assertIn('default_related_moves_ids', context)
        self.assertIn('default_related_moves_in', context)

        # Check if related moves are included in the context
        self.assertGreater(len(context['default_related_moves_ids']), 0)
        self.assertGreater(len(context['default_related_moves_in']), 0)

