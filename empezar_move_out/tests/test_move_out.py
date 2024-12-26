from datetime import datetime, timedelta
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError
from odoo import fields

class TestMoveOutModel(TransactionCase):

    def setUp(self):
        super().setUp()

        self.move_out_model = self.env['move.out']
        self.container_type_size = self.env["container.type.data"].create(
            {
                "name": "20FT",
                "company_size_type_code": "20FT",
                "is_refer": "yes",
            }
        )

        self.shipping_line = self.env['res.partner'].create({
            'name': 'Test Shipping Line',
            'shipping_line_name': 'Test Shipping Line',
            'is_shipping_line': True,
            'applied_for_interchange': 'yes'
        })

        self.container_master = self.env["container.master"].create(
            {
                "name": "GVTU3000389",
                "type_size": self.container_type_size.id,
                "shipping_line_id": self.shipping_line.id,
                "gross_wt": "123",
                "tare_wt": "123",
            }
        )



        self.mode = self.env["mode.options"].create({"name": "mode"})
        self.truck_mode = self.env["mode.options"].create({"name": "Truck"})
        self.rail_mode = self.env["mode.options"].create({"name": "Rail"})
        self.gate_pass = self.env["gate.pass.options"].create({"name": "Move In"})

        self.location_shipping_line = self.env["location.shipping.line.mapping"].create(
            {
                "shipping_line_id": self.shipping_line.id,
                "company_id": self.env.company.id,
                "refer_container":"yes"
            }
        )

        self.location = self.env["res.company"].create(
            {
                "name": "Test Location",
                "street": "Test Location",
                "active": True,
                "mode_ids": [(6, 0, [self.truck_mode.id])],
                "shipping_line_mapping_ids": [(6, 0, [self.location_shipping_line.id])],
                "laden_status_ids": [
                    (
                        6,
                        0,
                        [self.env["laden.status.options"].create({"name": "laden"}).id],
                    )
                ],
            }
        )

        self.container_inventory = self.env['container.inventory'].create({
            'container_master_id': self.container_master.id,
            'location_id': self.location.id,
            'name': 'GVTU3000389',
        })

        self.hold_reason = self.env["hold.reason"].create(
            {
                "company_id": self.location.id,
                "name": "hold reason 1",
            }
        )

        self.hold_release_container = self.env['hold.release.containers'].create({
            'container_id': self.container_master.id,
            'location_id': self.location.id,
            'hold_date': datetime.now() + timedelta(days=10),
            'hold_reason_id':self.hold_reason.id
        })

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
                "port_loading": self.port_loading.id,
                "port_discharge": self.port_discharge.id,
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

        self.damage_condition = self.env["damage.condition"].create(
            {"name": "Damage A", "damage_code": "Size/Type A", "active": True}
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
                "balance_containers": 5,
            }
        )

        self.container_number1 = self.env['container.number'].create({
            'name': 'EUJU1234567',
            'vessel_booking_id': self.booking.id,
            'is_unlink': False,
            'is_unlink_non_editable': False
        })

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

        self.move_out = self.move_out_model.create({
            'shipping_line_id': self.shipping_line.id,
            'inventory_id': self.container_inventory.id,
            'location_id': self.location.id,
            'container_id':self.container_master.id,
            'delivery_order_id': self.delivery_order.id,
            'move_out_date_time': fields.Datetime.now(),
            'movement_type': 'export_stuffing',
            'export_stuffing_to': 'factory',
            'mode': 'truck',
            'truck_number': 'TRK1234',
            'driver_name': 'John Doe',
            'driver_mobile_number': '1234567890',
            'driver_licence_no': 'LIC123456',
        })

    def test_onchange_container_no_shipping_line_visible(self):
        """Test that the shipping line visibility changes based on container data"""
        self.move_out._compute_original_shipping_line()
        self.move_out.onchange_container()
        self.assertFalse(self.move_out.is_shipping_line_visible, "Shipping line visibility should be False initially")

    def test_onchange_is_shipping_line_interchange(self):
        """Test that the shipping line visibility changes based on container data"""
        self.move_out.is_shipping_line_interchange = 'no'
        self.move_out.onchange_is_shipping_line_interchange()
        self.assertEqual(self.move_out.shipping_line_id.id, self.move_out.container_id.shipping_line_id.id)

    def test_onchange_shipping_line_interchange(self):
        """Test that the shipping line visibility changes based on container data"""
        self.move_out.is_shipping_line_interchange = 'yes'
        self.move_out.shipping_line_interchange()
        self.assertEqual(self.move_out.container_id.shipping_line_id.id, self.container_master.shipping_line_id.id)

    def test_compute_delivery_order_url(self):
        """Test that the delivery order URL is computed correctly"""

        self.move_out.delivery_order_id = self.delivery_order.id  # Link delivery order
        self.move_out._compute_delivery_order_url()
        self.assertIn('DO1234', self.move_out.delivery_order_url,
                      "Delivery order URL should contain the delivery number")

    def test_move_out_constraints(self):
        """Test the constraint on move_out_date_time field"""
        with self.assertRaises(ValidationError):
            self.move_out.write({'move_out_date_time': datetime.now() + timedelta(days=1)})  # Invalid datetime

    def test_check_container(self):
        """Test the check_container method for updating fields based on container status."""

        # Assign a container to the move_out record to trigger the onchange method
        self.move_out.container_id = self.container_master

        # Call the method
        self.move_out.check_container()

        # Validate the updates
        self.assertEqual(
            self.move_out.shipping_line_id.id,
            self.container_master.shipping_line_id.id,
            "Shipping line ID should match the container's shipping line ID."
        )

    # def test_cancel_edit(self):
    #     self.move_out.move_in_date_time = fields.Datetime.now()
    #     self.move_out.with_context({'is_edit_time':0}).cancel_edit()
    #     self.assertFalse(self.move_out.is_time_editable, "Time should not be editable after cancel_edit is called")

    def test_move_out_constraints_unique_shipping_line(self):
        """Test the uniqueness constraint for shipping line per inventory"""

        with self.assertRaises(ValidationError):
            self.move_out_model.create({
                'shipping_line_id': self.shipping_line.id,
                'inventory_id': self.container_inventory.id,
                'location_id': self.location.id,
                'move_out_date_time': fields.Datetime.now(),
                'movement_type': 'export_stuffing',
                'mode': 'truck'
            })

    def test_invalid_move_out_date(self):
        """Test move out record with an invalid move out date"""
        with self.assertRaises(ValidationError):
            self.move_out.write({
                'move_out_date_time': datetime(2025, 1, 1),  # Future date
            })

    def test_driver_mobile_number_format(self):
        """Test that the driver mobile number follows the expected format"""  # Invalid mobile number
        with self.assertRaises(ValidationError):
            self.move_out.driver_mobile_number = 'invalid_mobile'

    def test_check_move_out_date_time(self):
        """Test validation for move out date/time in the future."""
        future_date = datetime.now() + timedelta(days=1)
        self.move_out.move_out_date_time = future_date
        with self.assertRaises(ValidationError):
            self.move_out._check_move_out_date_time()

    def test_create_record_info(self):
        """Test computation of record creation info."""
        self.move_out._compute_get_create_record_info()
        self.assertTrue(self.move_out.display_create_info, "Create record info should not be empty")

    def test_modify_record_info(self):
        """Test computation of record modification info."""
        self.move_out.write({'shipping_line_id': self.shipping_line.id})  # Trigger modification
        self.move_out._compute_get_modify_record_info()
        self.assertTrue(self.move_out.display_modified_info, "Modify record info should not be empty")

    def test_gate_pass_generation(self):
        """Test generation of Gate Pass number."""
        self.move_out.gate_pass()
        self.assertTrue(self.move_out.gate_pass_no, "Gate Pass number should be generated")
        self.assertIn("GPMO2324", self.move_out.gate_pass_no, "Gate Pass number should start with the defined prefix")

    def test_report_file_name_formatting(self):
        """Test the correct formatting of report file name."""
        file_name = self.move_out._get_report_file_name()
        self.assertIn(self.move_out.container_id.name, file_name, "File name should include the container name")
        self.assertIn("GATEPASS", file_name, "File name should include 'GATEPASS'")

    def test_get_available_seal_count(self):
        """Test retrieval of available seal count."""
        self.env['seal.management'].create({
            "seal_number": 1234567890,
            'location': self.container_inventory.location_id.id,
            'shipping_line_id': self.shipping_line.id,
            'rec_status': 'available',
        })

        count = self.move_out_model._get_available_seal_count(
            self.container_inventory.location_id.id, self.shipping_line.id
        )
        self.assertEqual(count, 1, "Available seal count should match the expected value")

    def test_check_delivery_order_id_active(self):
        """Test to validate that the delivery order is active."""
        delivery_order_inactive = self.env["delivery.order"].create(
            {
                "delivery_no": "DO1235",
                "active":False,
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
                "container_details": [(6, 0, [self.container_delivery_detail.id])],
            }
        )

        with self.assertRaises(ValidationError):
            self.move_out.delivery_order_id = delivery_order_inactive.id

    def test_check_delivery_order_id_balance(self):
        """Test to ensure balance containers is not zero."""
        self.delivery_order.balance_containers = 0
        with self.assertRaises(ValidationError):
            self.move_out._check_delivery_order_id()

    def test_check_move_out_date_time(self):
        """Test to ensure move out date/time is not in the future."""
        with self.assertRaises(ValidationError):
            future_time = datetime.now() + timedelta(days=1)
            self.move_out.move_out_date_time = future_time

    def test_compute_get_create_record_info(self):
        """Test the computation of create record information."""
        self.move_out._compute_get_create_record_info()
        self.assertTrue(self.move_out.display_create_info)

    def test_validate_container_booking(self):
        """Test validation against booking number."""
        with self.assertRaises(ValidationError):
            self.move_out.booking_no_id = self.booking

    def test_download_gate_pass(self):
        """Test downloading the gate pass."""
        self.move_out.gate_pass_no = "GP123456"
        self.move_out.download_gate_pass()
        self.assertIsNotNone(self.move_out.gate_pass_no)

    def test_download_out_edi(self):
        """Test downloading EDI attachment."""
        self.move_out.edi_out_attachment_id = self.env['ir.attachment'].create({
            'name': 'Test EDI',
            'type': 'binary',
            'datas': b'Test Data',
            'res_model': 'move.out'
        })
        action = self.move_out.download_out_edi()
        self.assertIn('/web/content/', action['url'])

    def test_format_location_address(self):
        """Test formatting the location address."""
        formatted_address = self.move_out._format_location_address(self.location)
        self.assertIn(self.location.name, formatted_address)

    def test_get_report_file_name(self):
        """Test the report file name generation."""
        file_name = self.move_out._get_report_file_name()
        self.assertIn('GATEPASS_', file_name)

    def test_on_change_movement_type(self):
        """Test that fields are cleared correctly based on the selected movement type."""
        self.move_out.movement_type = 'export_stuffing'
        self.move_out.export_stuffing_to = 'factory'
        self.move_out.on_change_movement_type()

        self.assertFalse(self.move_out.to_port_id)
        self.assertFalse(self.move_out.to_terminal_id)
        self.assertFalse(self.move_out.to_empty_yard_id)

        self.move_out.movement_type = 'repo'
        self.move_out.on_change_movement_type()

        self.assertFalse(self.move_out.to_factory)
        self.assertFalse(self.move_out.to_cfs_icd_id)
    #
    def test_compute_balance_containers(self):
        """Test that balance containers are computed correctly."""
        # self.move_out.booking_no_id = self.booking.id
        self.move_out._compute_balance_containers()
        self.assertEqual(self.move_out.delivery_order_balance_and_type_sizes, '20FT (* 10)')

    #
    # def test_onchange_delivery_booking_no(self):
    #     """Test that transporter and exporter fields are updated correctly."""
    #     self.move_out.booking_no_id = self.booking.id
    #     self.move_out.onchange_delivery_booking_no()
    #     self.assertEqual(self.move_out.transporter_allocated_id, self.booking.transporter_name)
    #
    #     self.move_out.booking_no_id = False
    #     self.move_out.delivery_order_id = self.delivery_order
    #     self.move_out.onchange_delivery_booking_no()
    #     self.assertEqual(self.move_out.exporter_name_id, self.delivery_order.exporter_name)

    def test_gate_pass_visibility(self):
        """Test that gate pass visibility is correctly computed."""
        self.move_out.location_id = self.location
        self.move_out.shipping_line_id = self.location.shipping_line_mapping_ids.mapped('shipping_line_id')[0]
        self.move_out._compute_gate_pass_visibility()

    def test_validation_check_record_is_active_or_not(self):
        """Test validation for active records."""
        with self.assertRaises(ValidationError):
            self.move_out.transporter_allocated_id = self.env['res.partner'].create({
                'name': 'Inactive Transporter',
                'active': False
            })
            self.move_out.check_record_is_active_or_not()

    def test_compute_move_in_url(self):
        self.move_out.write({'move_in_id':self.move_in.id})
        self.move_out._compute_move_in_url()
        self.assertIn('GVTU3000389',self.move_out.move_in_url)

    # def test_compute_booking_number_url(self):
    #     self.move_out.write({'booking_no_id': self.booking.id})
    #     self.move_out._compute_booking_number_url()
    #     self.assertIn('BOOK001',self.move_out.booking_number_url)

    def test_validity_status_expired(self):
        """ Test validity status when the date has expired. """
        self.move_out.booking_validity_datetime = fields.Date.today() - timedelta(days=1)
        self.move_out._compute_validity_status()
        self.assertEqual(self.move_out.validity_status, 'Expired', "The validity status should be 'Expired'.")

    def test_validity_status_not_expired(self):
        """ Test validity status when the date is still valid. """
        self.move_out.booking_validity_datetime = fields.Date.today() + timedelta(days=1)
        self.move_out._compute_validity_status()
        self.assertEqual(self.move_out.validity_status, '', "The validity status should be empty for valid dates.")

    def test_compute_delivery_domain(self):
        """ Test delivery domain computation based on location and move in records. """
        self.move_out._compute_delivery_domain()
        self.assertEqual(self.delivery_order.id, self.move_out.delivery_order_compute_domain.id,"Delivery domain should include the valid delivery order.")


    def test_compute_booking_domain(self):
        """ Test booking domain computation based on location and move in records. """
        self.move_out._compute_booking_domain()
        self.assertEqual(self.booking.id, self.move_out.vessel_booking_compute_domain.id,"Booking domain should include the valid booking.")

    def test_onchange_truck_number(self):
        """Test the onchange method for truck_number field to ensure it converts to uppercase."""
        self.move_out.truck_number = 'truck123'
        self.move_out._onchange_truck_number()
        self.assertEqual(self.move_out.truck_number, 'TRUCK123', "Truck number should be converted to uppercase.")

    def test_onchange_wagon_number(self):
        """Test the onchange method for wagon_number field to ensure it converts to uppercase."""
        self.move_out.wagon_number = 'wagon123'
        self.move_out._onchange_wagon_number()
        self.assertEqual(self.move_out.wagon_number, 'WAGON123', "Wagon number should be converted to uppercase.")

    # def test_action_release_container_yes_release(self):
    #     """Test action_release_container when release_container is 'yes_release'."""
    #     # self.move_out.inventory_id = self.container_inventory.id
    #     self.hold_release_container.container_id = self.move_out.container_id.id
    #     self.move_out.release_container = 'yes_release'
    #     self.move_out.action_release_container()

    def test_action_release_container_cancel_on_hold(self):
        """Test action_release_container when release_container is 'cancel' and the container is on hold."""
        self.move_out.release_container = 'cancel'
        self.move_out.is_container_on_hold = True

        with self.assertRaises(ValidationError, msg="The container is on hold. A ValidationError should be raised."):
            self.move_out.action_release_container()

    def test_action_release_container_cancel_not_on_hold(self):
        """Test action_release_container when release_container is 'cancel' and the container is not on hold."""
        self.move_out.release_container = 'cancel'
        self.move_out.is_container_on_hold = False
        self.move_out.action_release_container()

    def test_seal_number_validation(self):
        """Test the constraint on seal numbers to ensure they are distinct."""

        # Assign seal numbers and check they are distinct
        self.move_out.write({'seal_no_1': 'SEAL001', 'seal_no_2': 'SEAL002'})
        self.move_out._check_seal_numbers()  # Should pass without issue

    def test_compute_mode_readonly(self):
        """Test that `mode` is correctly set based on location modes and the `is_mode_readonly` flag is updated."""
        self.assertEqual(self.move_out.mode, 'truck', "Mode should initially be set to 'truck'.")
        self.assertTrue(self.move_out.is_mode_readonly, "Mode should be readonly since there's only one mode.")

        # Add 'Rail' mode and check if it becomes editable
        self.location.write({'mode_ids': [(4, self.rail_mode.id)]})
        self.move_out._compute_make_mode_readonly()

        self.assertFalse(self.move_out.is_mode_readonly, "Mode should be editable with multiple modes available.")

    def test_compute_laden_status_readonly(self):
        """Test that `laden_status` is correctly set based on location laden statuses and the `is_laden_status_readonly` flag is updated."""
        laden_status_empty = self.env["laden.status.options"].create({"name": "empty"})
        self.location.write({'laden_status_ids': [(4, laden_status_empty.id)]})
        self.move_out._compute_make_laden_status_readonly()

        self.assertFalse(self.move_out.is_laden_status_readonly,
                         "Laden status should be editable with multiple options.")

    def test_rec_status_update_on_active(self):
        """Test the record status updates based on the 'active' field."""
        # self.move_out.active = True
        # self.move_out._compute_move_out_check_active_records()
        # self.assertEqual(self.move_out.rec_status, 'active',
        #                  "Record status should be 'active' when the record is active.")

        self.move_out.active = False
        self.move_out._compute_move_out_check_active_records()
        self.assertEqual(self.move_out.rec_status, 'disable',
                         "Record status should be 'disable' when the record is inactive.")

    def test_gross_and_tare_weight_validation(self):
        """Test the constraint and onchange on gross_wt and tare_wt."""
        # Test invalid negative weight
        with self.assertRaises(ValidationError):
            self.move_out.write({
                'gross_wt': -100,
            })

        # Test tare weight greater than gross weight
        with self.assertRaises(ValidationError):
            self.move_out.write({
                'gross_wt': 100,
                'tare_wt': 200,
            })

        # Ensure valid gross and tare weight
        self.move_out.write({
            'gross_wt': 300,
            'tare_wt': 100,
        })
        self.assertEqual(self.move_out.gross_wt, 300)
        self.assertEqual(self.move_out.tare_wt, 100)

    def test_temperature_validation(self):
        """Test the temperature validation and is_temperature flag."""
        # Test invalid temperature range
        with self.assertRaises(ValidationError):
            self.move_out.write({'temperature': 1000})
            self.move_out._compute_check_temperature_validations()


    def test_humidity_validation(self):
        """Test the humidity validation and is_humidity flag."""

        # Test invalid humidity range
        with self.assertRaises(ValidationError):
            self.move_out.write({'humidity': 1000})
            self.move_out._compute_check_humidity_validations()

    def test_vent_validation(self):
        """Test the vent validation and is_vent flag."""

        # Test invalid vent range
        with self.assertRaises(ValidationError):
            self.move_out.write({'vent': 1000})
            self.move_out._compute_check_vent_validations()

    def test_check_vent_seal_no_validations(self):
        self.move_out._compute_check_vent_seal_no_validations()
        self.assertTrue(self.move_out.is_vent_seal_number)
