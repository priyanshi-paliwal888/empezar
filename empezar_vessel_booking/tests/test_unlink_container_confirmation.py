from odoo.tests import common
from odoo.exceptions import ValidationError
from odoo import fields

class TestUnlinkContainerConfirmation(common.TransactionCase):

    def setUp(self):
        super(TestUnlinkContainerConfirmation, self).setUp()

        self.location = self.env["res.company"].create(
            {
                "name": "Test Company",
            }
        )

        self.unlink_reason_update = self.env['unlink.reason'].create({
            'reason': 'Damaged',
            'update_quantity': True
        })

        self.unlink_reason_no_update = self.env['unlink.reason'].create({
            'reason': 'Incorrect Entry',
            'update_quantity': False
        })

        self.type_size = self.env['container.type.data'].create({
            'name': '20 FT',
            'company_size_type_code': '20FT',
            'is_refer': 'no',
            'active': True,
            'company_id': self.env.company.id
        })

        self.container_master = self.env['container.master'].create({
            'name': 'GVTU3000389',
            'type_size': self.type_size.id
        })

        self.container_detail = self.env['container.details'].create({
            'container_size_type': self.type_size.id,
            'container_qty': 10
        })

        self.partner_shipping_line = self.env['res.partner'].create({
            'name': 'Shipping Line',
            'is_shipping_line': True,
        })

        self.partner_transporter = self.env['res.partner'].create({
            'name': 'Transporter',
            'parties_type_ids': [(0, 0, {'name': 'Transporter'})],
        })

        self.vessel_booking = self.env['vessel.booking'].create({
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
        })

        self.container_number1 = self.env['container.number'].create({
            'name': 'GVTU3000389',
            'vessel_booking_id': self.vessel_booking.id,
            'is_unlink': False,
            'is_unlink_non_editable': False
        })

    def test_confirm_unlink_with_quantity_update(self):
        """
        Test confirm_unlink method when unlink_reason requires quantity update.
        """
        wizard = self.env['unlink.container.confirmation'].create({
            'container_ids': [(6, 0, [self.container_number1.id])],
            'unlink_reason': self.unlink_reason_update.id
        })
        wizard.confirm_unlink()

        self.assertEqual(self.container_number1.unlink_reason.id, self.unlink_reason_update.id)
        self.assertTrue(self.container_number1.is_unlink_non_editable)
        container_detail = self.env['container.details'].search([
            ('booking_id', '=', self.vessel_booking.id),
            ('container_size_type', '=', self.type_size.id)
        ])
        self.assertEqual(container_detail.container_qty, 9)  # Decreased by 1

    def test_confirm_unlink_without_quantity_update(self):
        """
        Test confirm_unlink method when unlink_reason does not require quantity update.
        """
        wizard = self.env['unlink.container.confirmation'].create({
            'container_ids': [(6, 0, [self.container_number1.id])],
            'unlink_reason': self.unlink_reason_no_update.id
        })
        wizard.confirm_unlink()

        self.assertEqual(self.container_number1.unlink_reason.id, self.unlink_reason_no_update.id)
        self.assertTrue(self.container_number1.is_unlink_non_editable)
        container_detail = self.env['container.details'].search([
            ('booking_id', '=', self.vessel_booking.id),
            ('container_size_type', '=', self.type_size.id)
        ])

        self.assertEqual(container_detail.container_qty, 10)  # No change in quantity
