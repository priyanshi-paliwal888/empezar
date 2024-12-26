from datetime import datetime, timedelta, date
from odoo.tests.common import TransactionCase
from odoo import fields


class TestMoveInInvoiceDetails(TransactionCase):

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

        self.container_delivery_detail = self.env["container.details.delivery"].create(
            {
                "container_qty": 10,
                "balance_container": 5,
                "quantity": 5,
                "container_size_type": self.container_type.id,
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

        # Create a sample GST record
        self.gst_details = self.env["gst.details"].create(
            {
                "tax_payer_type": "Regular",
                "nature_of_business": "Trading",
                "state_jurisdiction": "Karnataka",
                "additional_place_of_business": "Warehouse A",
                "last_update": "01-01-2023",
            }
        )

        # Create a sample Partner record
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "is_cms_parties": True,
                "is_this_billed_to_party": "yes",
                "street": "123 Test Street",
                "gst_state": "Karnataka",
            }
        )

        # Create a sample Product Template
        self.product = self.env["product.template"].create(
            {
                "name": "Test Product",
                "gst_applicable": "yes",
                "charge_name": "Handling Charge",
            }
        )

        # Create an Invoice Detail record
        self.invoice_detail = self.env["move.in.invoice.details"].create(
            {
                "move_in_id": self.move_in.id,
                "invoice_number": "INV12345",
                "invoice_date": date.today(),
                "charge_id": self.product.id,
                "billed_to_party": self.partner.id,
                "billed_to_gst_no": self.gst_details.id,
                "amount": 10000,
            }
        )

    def test_compute_invoice_details(self):
        """Test the computation of invoice_details field."""
        self.invoice_detail._compute_invoice_details()
        expected_details = (
            f"INV12345 {self.invoice_detail.invoice_date.strftime('%d-%m-%Y')}"
        )
        self.assertEqual(
            self.invoice_detail.invoice_details,
            expected_details,
            "Invoice details should be correctly computed",
        )

    def test_compute_party_invoice_type(self):
        """Test the computation of party_invoice_type field."""
        self.invoice_detail._compute_party_invoice_type()
        expected_party_invoice_type = (
            f"{self.partner.name} {self.invoice_detail.invoice_type}"
        )
        self.assertEqual(
            self.invoice_detail.party_invoice_type,
            expected_party_invoice_type,
            "Party invoice type should be correctly computed",
        )

    def test_remarks_for_gst_no(self):
        """Test remarks when GST is not applicable."""
        self.invoice_detail.is_gst_applicable = "no"
        self.invoice_detail._compute_remarks_display()
        expected_remarks = (
            "SUPPLY MEANT FOR EXPORT UNDER LETTER OF UNDERTAKING WITHOUT PAYMENT OF GST"
        )
        self.assertEqual(
            self.invoice_detail.remarks,
            expected_remarks,
            "Remarks should be for export without GST payment",
        )

    def test_remarks_for_gst_yes(self):
        """Test remarks when GST is applicable."""
        self.invoice_detail.is_gst_applicable = "yes"
        self.invoice_detail.gst_rate = self.env["account.tax"].create(
            {
                "name": "18%",
                "amount": 18,
                "type_tax_use": "sale",
                "active": True,
            }
        )
        self.invoice_detail._compute_remarks_display()
        expected_remarks = (
            f"EXPORT UNDER LUT BOND. ARN NO. "
            f"DATED: (IGST @{self.invoice_detail.gst_rate.name} IGST AMOUNT: {self.invoice_detail.amount}) "
            f"SUPPLY MEANT FOR EXPORT UNDER LETTER OF UNDERTAKING WITHOUT PAYMENT OF GST"
        )
        self.assertEqual(
            self.invoice_detail.remarks,
            expected_remarks,
            "Remarks should reflect GST applicable information",
        )

    def test_cancel_invoice_action(self):
        """Test the cancel_invoice action method."""
        result = self.invoice_detail.cancel_invoice()
        self.assertEqual(
            result["name"],
            "Cancel Invoice",
            "The action should be for 'Cancel Invoice'",
        )
        # self.assertEqual(
        #     result["res_model"],
        #     "invoice.cancellation.wizard",
        #     "The model should be 'invoice.cancellation.wizard'",
        # )
        self.assertEqual(
            result["context"]["default_invoice_id"],
            self.invoice_detail.id,
            "The context should contain the correct invoice ID",
        )

    def test_generate_pdf(self):
        """Test that PDF generation is triggered correctly."""
        result = self.invoice_detail.generate_pdf()
        self.assertTrue(result)
