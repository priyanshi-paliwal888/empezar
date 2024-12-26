from datetime import datetime, timedelta
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from odoo import fields


class TestMoveIn(TransactionCase):

    def setUp(self):
        super().setUp()

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

        self.shipping_line_1 = self.env["res.partner"].create(
            {
                "name": "Test Shipping Line",
                "company_id": self.env.company.id,
            }
        )

        self.location_shipping_line = self.env["location.shipping.line.mapping"].create(
            {
                "shipping_line_id": self.shipping_line.id,
                "company_id": self.env.company.id,
            }
        )

        self.location = self.env["res.company"].create(
            {
                "name": "Test Location",
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

        self.container_type_size = self.env["container.type.data"].create(
            {
                "name": "20FT",
                "company_size_type_code": "20FT",
                "is_refer": "no",
            }
        )

        self.partner_transporter = self.env["res.partner"].create(
            {
                "name": "Transporter",
                "parties_type_ids": [(0, 0, {"name": "Transporter"})],
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

        self.container_type = self.env["container.type.data"].create(
            {
                "name": "20 FT",
                "company_size_type_code": "20FT",
                "is_refer": "no",
                "active": True,
                "company_id": self.env.company.id,
            }
        )

        # Create Container Detail
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
                "balance_container": 5,
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
                "balance_containers": 5,
            }
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

        self.delivery_order = self.env["delivery.order"].create(
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
                "container_details": [(6, 0, [self.container_delivery_detail.id])],
            }
        )

        self.move_in = self.env["move.in"].create(
            {
                "container": "GVTU3000389",
                "location_id": self.location.id,
                "do_no_id": self.delivery_order.id,
                "booking_no_id": self.booking.id,
                "mode": "truck",
                "damage_condition": self.damage_condition.id,
                "shipping_line_id": self.shipping_line.id,
                "type_size_id": self.container_type_size.id,
                "grade": "a",
            }
        )

    def test_default_get(self):
        """Test that default values for 'mode' and 'laden_status' are set based on 'location_id'."""
        default_location = self.env["res.company"].sudo().search([("id", "=", 1)])
        laden = self.env["laden.status.options"].create({"name": "laden"})
        default_location.write(
            {
                "mode_ids": [(6, 0, [self.truck_mode.id])],
                "laden_status_ids": [(6, 0, [laden.id])],
            }
        )
        default_values = self.env["move.in"].default_get(
            ["location_id", "mode", "laden_status"]
        )
        self.assertEqual(default_values["mode"], "truck")

    def test_compute_make_mode_readonly(self):
        """Test that the mode is set correctly based on location mode and is_mode_readonly flag."""
        self.location.write({"mode_ids": [(6, 0, [self.truck_mode.id])]})
        self.move_in._compute_make_mode_readonly()
        self.assertEqual(self.move_in.mode, "truck")
        self.assertTrue(self.move_in.is_mode_readonly)

        # Test both rail and truck
        self.location.write(
            {"mode_ids": [(6, 0, [self.rail_mode.id, self.truck_mode.id])]}
        )
        self.move_in._compute_make_mode_readonly()
        self.assertFalse(self.move_in.is_mode_readonly)

    def test_check_record_is_active_or_not(self):
        """Test that validation error is raised for inactive related fields."""
        inactive_party = self.env["res.partner"].create(
            {
                "name": "Inactive Party",
                "active": False,
            }
        )

        with self.assertRaises(ValidationError):
            self.move_in.write({"billed_to_party": inactive_party.id})

    def test_onchange_patch_count(self):
        """Test the patch count validation."""

        with self.assertRaises(ValidationError):
            self.move_in.write({"patch_count": 10000})

    # def test_compute_is_invoice_applicable(self):
    #     """Test that the invoice applicability is computed based on location and shipping line."""
    #     self.location.write(
    #         {
    #             "invoice_setting_ids": [
    #                 (
    #                     0,
    #                     0,
    #                     {
    #                         "inv_shipping_line_id": self.shipping_line.id,
    #                         "inv_applicable_at_location_ids": [
    #                             (
    #                                 6,
    #                                 0,
    #                                 [
    #                                     self.env["invoice.applicable.options"]
    #                                     .create({"name": "Test Inv applicable"})
    #                                     .id
    #                                 ],
    #                             )
    #                         ],
    #                     },
    #                 )
    #             ]
    #         }
    #     )
    #     self.move_in.write({"shipping_line_id": self.shipping_line.id})
    #     self.move_in._compute_is_invoice_applicable()
    #     self.assertTrue(self.move_in.is_invoice_applicable)

    def test_compute_gate_pass_visibility(self):
        """Test gate pass visibility based on location and shipping line mapping."""
        self.location.write(
            {
                "shipping_line_mapping_ids": [
                    (
                        0,
                        0,
                        {
                            "shipping_line_id": self.shipping_line_1.id,
                            "gate_pass_ids": [(6, 0, [self.gate_pass.id])],
                        },
                    )
                ]
            }
        )
        self.move_in.write({"shipping_line_id": self.shipping_line_1.id})
        self.move_in._compute_gate_pass_visibility()
        self.assertTrue(self.move_in.gate_pass_visible)

    def test_compute_display_name(self):
        """Test that display name is computed correctly based on container."""
        self.move_in._compute_display_name()
        expected_name = f"{self.container_master.name}({self.container_type_size.company_size_type_code})"
        self.assertEqual(self.move_in.display_name, expected_name)

    def test_compute_display_name_container(self):
        """Test that display name is computed correctly based on container."""
        self.container_type_size.company_size_type_code = False
        self.move_in._compute_display_name()
        self.assertEqual("GVTU3000389", self.move_in.display_name)

    def test_check_gross_and_tare_weight(self):
        """Test weight validations for gross and tare weight."""
        # Invalid tare weight greater than gross weight
        with self.assertRaises(ValidationError):
            self.move_in.write({"gross_wt": "100000000012", "tare_wt": "100000000013"})
            self.move_in.onchange_gross_and_tare_weight()

        # Valid tare and gross weight
        self.move_in.write({"gross_wt": "42", "tare_wt": "22"})
        self.move_in.onchange_gross_and_tare_weight()

    def test_check_move_in_date_time(self):
        """Test validation for move in date time."""
        future_date = fields.Datetime.now() + timedelta(days=1)
        with self.assertRaises(ValidationError):
            self.move_in.write({"move_in_date_time": future_date})
            self.move_in._check_move_in_date_time()

    def test_gate_pass_number_generation(self):
        """Test that gate pass number is generated correctly."""
        self.move_in.write({"location_id": self.location.id})
        self.move_in.gate_pass()
        self.assertTrue(self.move_in.gate_pass_no)

    def test_get_report_file_name(self):
        """Test the format of generated report file name."""
        self.move_in.write({"move_in_date_time": fields.Datetime.now()})
        expected_filename = f"GATEPASS_{self.move_in.container}_"
        self.assertIn(expected_filename, self.move_in._get_report_file_name())

    def test_get_booking_balance_container(self):
        """Test that gate pass number is generated correctly."""
        self.move_in.write({"booking_no_id": self.booking.id})
        self.move_in._compute_balance_containers()
        self.assertEqual(self.move_in.booking_balance_container, "20FT (*5)")

    def test_get_booking_number_url(self):
        """Test that gate pass number is generated correctly."""
        self.move_in.write({"booking_no_id": self.booking.id})
        self.move_in._compute_booking_number_url()
        self.assertIn("vessel.booking", self.move_in.booking_number_url)

    def test_get_delivery_order_url(self):
        self.move_in._compute_delivery_order_url()
        self.assertIn(
            self.move_in.do_no_id.delivery_no, self.move_in.delivery_order_url
        )

    def test_get_validity_status(self):
        self.move_in._compute_validity_status()
        self.assertEqual("", self.move_in.validity_status)

    def test_get_validity_expire_status(self):
        self.move_in.write(
            {"do_validity_datetime": datetime.today() - timedelta(days=5)}
        )
        self.move_in._compute_validity_status()
        self.assertEqual("Expired", self.move_in.validity_status)

    def test_get_seal_no(self):
        self.move_in.write({"movement_type": "factory_return", "is_seal_return": "no"})
        self.move_in.onchange_is_seal_return()
        self.assertFalse(self.move_in.seal_no_1)

    def test_get_seal_no_1(self):
        seal = self.env["seal.management"].create(
            {
                "seal_number": 1234567890,
                "shipping_line_id": self.shipping_line_1.id,
                "location": self.location.id,
            }
        )
        self.move_in.write(
            {
                "seal_no_1": 1234567890,
                "movement_type": "factory_return",
                "is_seal_return": "yes",
            }
        )
        self.move_in.change_seal_status()
        self.assertEqual("available", seal.rec_status)
        self.assertEqual("-", seal.container_number)

    def test_get_modify_record_info(self):
        self.move_in._get_modify_record_info()
        self.assertTrue(self.move_in.display_modified_info)

    def test_get_create_record_info(self):
        self.move_in._get_create_record_info()
        self.assertTrue(self.move_in.display_create_info)

    def test_get_do_balance_container(self):
        self.move_in._get_do_balance_container()
        self.assertEqual("20FT (* 10)", self.move_in.do_balance_container)

    def test_changes_in_mode(self):
        self.move_in.mode = "rail"
        self.move_in.changes_in_mode()
        self.assertFalse(self.move_in.truck_no)
        self.assertFalse(self.move_in.driver_name)
        self.assertFalse(self.move_in.transporter_allotment_id)

    def test_check_drive_mobile_no_validations(self):
        with self.assertRaises(ValidationError):
            self.move_in.write({"mode": "truck", "driver_mobile_no": 123})

    def test_check_drive_mobile_no_validations_invalid(self):
        with self.assertRaises(ValidationError):
            self.move_in.write({"mode": "truck", "driver_mobile_no": "AAABBBCCCD"})

    # def test_check_rec_status_active(self):
    #     self.move_in.write({"active": True})
    #     self.move_in._compute_move_in_check_active_records()
    #     self.assertEqual("active", self.move_in.rec_status)

    def test_check_rec_status_disable(self):
        self.move_in.write({"active": False})
        self.move_in._compute_move_in_check_active_records()
        self.assertEqual("disable", self.move_in.rec_status)

    def test_get_shipping_line_domain(self):
        self.move_in._compute_shipping_line_domain()
        self.assertEqual("Test Shipping Line", self.move_in.shipping_line_domain.name)

    def test_get_change_location_id(self):
        self.move_in.with_context(is_location_change=True).on_change_location_id()
        self.assertEqual("Test Shipping Line", self.move_in.shipping_line_id.name)

    def test_get_laden_status(self):
        self.move_in.make_laden_status_readonly()
        self.assertEqual("empty", self.move_in.laden_status)
        self.assertTrue(self.move_in.is_laden_status_readonly)

    def test_get_laden_status_laden(self):
        self.location.write(
            {
                "laden_status_ids": [
                    (
                        6,
                        0,
                        [self.env["laden.status.options"].create({"name": "Laden"}).id],
                    )
                ],
            }
        )
        self.move_in.make_laden_status_readonly()
        self.assertEqual("laden", self.move_in.laden_status)
        self.assertTrue(self.move_in.is_laden_status_readonly)

    def test_patch_count_visibility(self):
        self.move_in.patch_count_visibility()

    def test_check_digit_validation_for_container(self):
        self.move_in.check_digit_validation_for_container()
        self.assertFalse(self.move_in.is_patch_count_visible)

    def test_check_digit_validation_for_container_with_refer(self):
        self.move_in.type_size_id.is_refer = "yes"
        self.move_in.check_digit_validation_for_container()

    def test_update_container_master_with_all_fields(self):
        """Test updating all possible fields in the container master."""

        # Call the method with all fields provided
        result = self.env["move.in"].update_container_master(
            rec_container="GVTU3000389",
            rec_production_month="06",
            rec_production_year="2023",
            rec_gross_weight="12000",
            rec_tare_weight="3000",
        )

        self.assertTrue(
            result, "The method should return True when the update is successful"
        )
        self.assertEqual(
            self.container_master.month, "06", "Production month should be updated"
        )
        self.assertEqual(
            self.container_master.year, "2023", "Production year should be updated"
        )
        self.assertEqual(
            self.container_master.gross_wt, 12000, "Gross weight should be updated"
        )
        self.assertEqual(
            self.container_master.tare_wt, 3000, "Tare weight should be updated"
        )

    def test_gate_pass_no_not_generated(self):
        with self.assertRaises(ValidationError):
            self.move_in.download_gate_pass()

    def test_gate_pass_no_generated(self):
        self.move_in.gate_pass_no = "GP123456"
        report_action = self.env.ref("empezar_move_in.move_in_report_action")
        result = self.move_in.download_gate_pass()
        self.assertEqual(
            result["context"]["report_action"]["report_name"],
            "empezar_move_in.report_move_in_document",
        )

    def test_field_visibility_and_requirements(self):
        """Test the computation of field visibility and required fields based on location settings."""
        self.location.write(
            {
                "movement_move_in_settings_ids": [
                    (
                        0,
                        0,
                        {
                            "field_name": self.env["ir.model.fields"]
                            .search(
                                [
                                    ("name", "=", "mode"),
                                    ("model_id.name", "=", "Move In"),
                                ],
                                limit=1,
                            )
                            .id,
                            "movement_type": "move_in",
                        },
                    )
                ]
            }
        )
        self.move_in._compute_field_visibility_required()
        self.assertIn("mode", self.move_in.field_visibility)

    def test_edit_time(self):
        """Test that the 'edit_time' method sets 'is_time_editable' to True when context allows editing."""
        self.env.context = {"is_edit_time": 1}
        self.move_in.edit_time()
        self.assertTrue(self.move_in.is_time_editable)

    #
    def test_cancel_edit(self):
        """Test that 'cancel_edit' method sets 'is_time_editable' to False when context does not allow editing."""
        self.env.context = {"is_edit_time": 0}
        self.move_in.move_in_date_time = fields.Datetime.now()
        self.move_in.cancel_edit()
        self.assertFalse(self.move_in.is_time_editable)
