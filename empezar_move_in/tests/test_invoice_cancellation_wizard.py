from odoo.tests.common import TransactionCase
from odoo import fields


class TestInvoiceCancellationWizard(TransactionCase):

    def setUp(self):
        super().setUp()

        # Create a demo partner (for billed_to_party)
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "is_cms_parties": True,
                "is_this_billed_to_party": "yes",
            }
        )

        # Create a demo charge (product template)
        self.charge = self.env["product.template"].create(
            {
                "name": "Test Charge",
                "gst_applicable": "yes",
            }
        )

        # Create a demo GST record
        self.gst_details = self.env["gst.details"].create(
            {
                "tax_payer_type": "Regular",
            }
        )

        self.location = self.env["res.company"].create(
            {"name": "Test Location", "active": True}
        )

        self.damage_condition = self.env["damage.condition"].create(
            {"name": "Damage A", "damage_code": "Size/Type A", "active": True}
        )

        self.shipping_line = self.env["res.partner"].create(
            {
                "name": "Test Shipping Line",
                "company_id": self.env.company.id,
            }
        )

        self.container_type_size = self.env["container.type.data"].create(
            {
                "name": "20FT",
                "company_size_type_code": "20FT",
                "is_refer": "no",
            }
        )

        self.move_in = self.env["move.in"].create(
            {
                "container": "GVTU3000389",
                "location_id": self.location.id,
                "mode": "truck",
                "damage_condition": self.damage_condition.id,
                "shipping_line_id": self.shipping_line.id,
                "type_size_id": self.container_type_size.id,
                "grade": "a",
            }
        )

        # Create a move.in.invoice.details record to be cancelled
        self.invoice = self.env["move.in.invoice.details"].create(
            {
                "move_in_id": self.move_in.id,
                "invoice_number": "INV123",
                "invoice_date": fields.Date.today(),
                "billed_to_party": self.partner.id,
                "charge_id": self.charge.id,
                "billed_to_gst_no": self.gst_details.id,
                "amount": 1000,
                "invoice_status": "active",  # Initially active
            }
        )

        # Create the wizard record for cancellation
        # self.wizard = self.env["invoice.cancellation.wizard"].create(
        #     {
        #         "invoice_id": self.invoice.id,
        #         "cancellation_reason": "duplicate",
        #         "cancellation_remarks": "Duplicate entry",
        #     }
        # )

    def test_confirm_cancellation(self):
        """Test the cancellation of an invoice"""

        # Call the confirm_cancellation method
        self.wizard.confirm_cancellation()

        # Check that the invoice status has been updated to 'cancelled'
        self.assertEqual(
            self.invoice.invoice_status,
            "cancelled",
            "The invoice status should be 'cancelled'.",
        )

    def test_confirm_cancellation_no_invoice(self):
        """Test that cancellation does not proceed when no invoice is provided"""

        # Create a wizard without an invoice
        # wizard_no_invoice = self.env["invoice.cancellation.wizard"].create(
        #     {
        #         "invoice_id": False,
        #         "cancellation_reason": "duplicate",
        #         "cancellation_remarks": "No invoice provided",
        #     }
        # )

        # Call the confirm_cancellation method
        wizard_no_invoice.confirm_cancellation()

        # Ensure that no changes have been made to the invoice's status
        self.assertEqual(
            self.invoice.invoice_status,
            "active",
            "The invoice status should remain 'active' when no invoice is provided.",
        )

    def test_cancellation_with_remarks(self):
        """Test that cancellation remarks are correctly set"""

        # Ensure the wizard has the correct remarks
        self.assertEqual(
            self.wizard.cancellation_remarks,
            "Duplicate entry",
            "The cancellation remarks should be 'Duplicate entry'.",
        )

        # Call the confirm_cancellation method
        self.wizard.confirm_cancellation()

        # Ensure the invoice status is 'cancelled' after the cancellation process
        self.assertEqual(
            self.invoice.invoice_status, "cancelled", "The invoice should be cancelled."
        )
