from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from odoo import fields
from datetime import timedelta


class TestVesselBooking(TransactionCase):

    def setUp(self):
        super(TestVesselBooking, self).setUp()

        # Create Shipping Line partner
        self.partner_shipping_line = self.env['res.partner'].create({
            'name': 'Shipping Line',
            'is_shipping_line': True,
        })

        # Create Transporter partner
        self.partner_transporter = self.env['res.partner'].create({
            'name': 'Transporter',
            'parties_type_ids': [(0, 0, {'name': 'Transporter'})],
        })

        # Create Location
        self.location = self.env['res.company'].create({
            'name': 'Location',
        })

        # Create Container Type
        self.container_type = self.env['container.type.data'].create({
            'name': '20 FT',
            'company_size_type_code': '20FT',
            'is_refer': 'no',
            'active': True,
            'company_id': self.env.company.id
        })

        self.container_type_2 = self.env['container.type.data'].create({
            'name': '30 FT',
            'company_size_type_code': '30FT',
            'is_refer': 'no',
            'active': True,
            'company_id': self.env.company.id
        })

        self.container_type_3 = self.env['container.type.data'].create({
            'name': '30 FT',
            'company_size_type_code': '30FT',
            'is_refer': 'no',
            'active': True,
            'company_id': self.env.company.id
        })

        # Create Container Detail
        self.container_detail = self.env['container.details'].create({
            'container_size_type': self.container_type.id,
            'container_qty': 10,
            'balance': 5,
        })

        # Create Container Numbers
        self.container_number1 = self.env['container.number'].create({
            'name': 'GVTU3000389',
            'unlink_reason': False,
            'is_unlink': False,
            'is_unlink_non_editable': False
        })

        # Create Vessel Booking with Container Details
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
            'container_details': [(6, 0, [self.container_detail.id])],  # Add container details
            'container_numbers': [(6, 0, [self.container_number1.id])]  # Add container numbers
        })

    def test_vessel_booking(self):
        """
        Test creation of vessel booking with container details and container numbers.
        """
        vessel_booking = self.env['vessel.booking'].create({
            'shipping_line_id': self.partner_shipping_line.id,
            'transporter_name': self.partner_transporter.id,
            'location': [(6, 0, [self.location.id])],
            'booking_no': 'BKG12345',
            'booking_date': fields.Date.today(),
            'validity_datetime': fields.Datetime.now(),
            'cutoff_datetime': fields.Datetime.now(),
            'container_details': [(6, 0, [self.container_detail.id])],  # Add container details
            'container_numbers': [(6, 0, [self.container_number1.id])]  # Add container numbers
        })

        # Test if vessel booking is created with container details and container numbers
        self.assertEqual(len(vessel_booking.container_numbers), 1)

    def test_get_modify_record_info(self):
        """
        Test the '_get_modify_record_info' method.
        """
        # Simulate record modification
        self.booking.write({'vessel': 'Modified Vessel'})
        self.booking._get_modify_record_info()
        # Assert that the modified info is correctly updated
        self.assertTrue(self.booking.display_modified_info)

    def test_get_create_record_info(self):
        """
        Test the '_get_create_record_info' method.
        """
        self.booking._get_create_record_info()
        # Assert that the creation info is correctly updated
        self.assertTrue(self.booking.display_create_info)

    def test_check_active_records(self):
        """
        Test the '_check_active_records' method.
        """
        self.booking._check_active_records()
        # Assert that the status is 'active'
        self.assertEqual(self.booking.rec_status, 'active')

        # Deactivate the record
        self.booking.write({'active': False})
        self.booking._check_active_records()
        # Assert that the status is 'disable'
        self.assertEqual(self.booking.rec_status, 'disable')

    def test_download_container_record(self):
        """
        Test the 'download_container_record' method.
        """
        # Call the method to download container records
        result = self.booking.download_container_record()
        # Assert that the result is a URL action to download a file
        self.assertEqual(result['type'], 'ir.actions.act_url')
        self.assertIn('download=true', result['url'])

    def test_download_booking_xlsx_file(self):
        """
        Test the 'download_booking_xlsx_file' method.
        """
        # Call the method to download the booking file
        result = self.booking.download_booking_xlsx_file()
        # Assert that the result is a URL action to download a file
        self.assertEqual(result['type'], 'ir.actions.act_url')
        self.assertIn('download=true', result['url'])

    def test_unique_booking_no_shipping_line(self):
        """
        Test unique constraint on booking_no and shipping_line_id.
        """
        with self.assertRaises(ValidationError):
            self.env['vessel.booking'].create({
                'shipping_line_id': self.partner_shipping_line.id,
                'location': [(6, 0, [self.location.id])],
                'transporter_name': self.partner_transporter.id,
                'booking_no': 'BOOK001',
                'booking_date': fields.Date.today(),
                'validity_datetime': fields.Datetime.now(),
                'cutoff_datetime': fields.Datetime.now(),
                'vessel': 'Duplicate Vessel',
                'voyage': '54321',
                'container_details': [(6, 0, [self.container_detail.id])],  # Add container details
                'container_numbers': [(6, 0, [self.container_number1.id])]  # Add container numbers
            })

    def test_check_booking_date(self):
        """
        Test constraint on booking_date to ensure it is not in the future.
        """
        future_date = fields.Date.today() + timedelta(days=1)
        with self.assertRaises(ValidationError):
            self.booking.write({'booking_date': future_date})

    def test_check_validity_datetime(self):
        """
        Test the constraint that ensures validity_datetime is greater than booking_date.
        """
        past_validity = fields.Datetime.now() - timedelta(days=1)
        with self.assertRaises(ValidationError):
            self.booking.write({'validity_datetime': past_validity})

    def test_check_cutoff_datetime(self):
        """
        Test the constraint that ensures cutoff_datetime is greater than booking_date.
        """
        past_cutoff = fields.Datetime.now() - timedelta(days=1)
        with self.assertRaises(ValidationError):
            self.booking.write({'cutoff_datetime': past_cutoff})

    def test_total_containers(self):
        """
        Test the computation of total containers.
        """
        container_detail = self.env['container.details'].create({
            'container_size_type': self.container_type_2.id,
            'container_qty': 10,
            'booking_id': self.booking.id,
        })
        self.booking._get_total_containers()
        self.assertEqual(self.booking.total_containers, 20)

    def test_balance_containers(self):
        """
        Test the computation of balance containers.
        """
        container_detail = self.env['container.details'].create({
            'container_size_type': self.container_type_3.id,
            'balance': 5,
            'booking_id': self.booking.id,
            'container_qty': 2,
        })
        self.booking._get_total_balance_container()
        self.assertEqual(self.booking.balance_containers, 10)

    def test_compute_display_info(self):
        """
        Test the '_compute_display_info' method.
        """
        # Compute display info
        self.booking._compute_display_info()

        # Assert that display info fields are correctly populated
        self.assertTrue(self.booking.display_create_info)
        self.assertTrue(self.booking.display_modified_info)

    def test_compute_location_shipping_line(self):
        """
        Test the '_compute_location_shipping_line' method.
        """
        # Test case where no location is selected
        with self.assertRaises(ValidationError):
            self.booking.write({'location': [(5, 0, 0)]})  # Remove location

        self.booking.write({
            'location': [(6, 0, [self.location.id])],
        })
        self.booking._compute_location_shipping_line()
        self.assertIn('is_refer', self.booking.refer_container_selection)
