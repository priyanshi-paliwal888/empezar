from odoo.tests import common
from odoo.exceptions import ValidationError
import os
from datetime import datetime
from unittest.mock import patch
from pytz import timezone as pytz


class TestResPartnerProfile(common.TransactionCase):

    def setUp(self):
        super(TestResPartnerProfile, self).setUp()
        # Initialize the required resources for tests
        self.partner_model = self.env['res.partner']
        self.shipping_tag_id = self.env.ref('empezar_base.res_partner_shipping_tag_1')
        self.cms_tag_id = self.env.ref('empezar_base.res_partner_cms_parties_tag_1')

    def test_partner_create_shipping_line(self):
        """ Tests if creating a partner from the shipping line view sets necessary fields. """
        context = {'is_shipping_view': True}
        vals = {
            'shipping_line_name': 'New Shipping Line',
        }

        partner = self.partner_model.with_context(context).create(vals)
        self.assertTrue(partner.is_shipping_line)
        self.assertEqual(partner.name, partner.shipping_line_name)
        self.assertIn(self.shipping_tag_id, partner.category_id)

    def test_partner_write_shipping_line_name(self):
        """ Tests if updating the shipping line name updates the partner's name in shipping line view. """
        partner = self.partner_model.create({
            'name': 'Old Line Name',
            'shipping_line_name': 'Line to Update',
        })

        context = {'is_shipping_view': True}
        vals = {'shipping_line_name': 'Updated Line Name'}
        partner.with_context(context).write(vals)
        self.assertEqual(partner.name, partner.shipping_line_name)
        self.assertEqual(partner.shipping_line_name, 'Updated Line Name')

    def test_partner_validate_logo_size(self):
        """ Tests if the logo size validation works correctly for exceeding 1MB. """
        image_path = os.path.join(os.path.dirname(__file__), 'img/sample_img_2mb.png')
        with open(image_path, "rb") as f:
            image_data = f.read()

        with self.assertRaises(ValidationError) as e:
            self.partner_model.create({
                'name': 'Test Partner',
                'logo': image_data
            })
        self.assertEqual(e.exception.args[0], "Image size cannot exceed 1MB.")

    def test_partner_create_cms_parties(self):
        """ Tests if creating a partner from the CMS parties view sets necessary fields. """
        context = {'is_cms_parties_view': True}
        vals = {
            'party_name': 'New CMS Party',
        }

        partner = self.partner_model.with_context(context).create(vals)

        self.assertTrue(partner.is_cms_parties)
        self.assertEqual(partner.name, partner.party_name)
        self.assertIn(self.cms_tag_id, partner.category_id)

    def test_partner_write_cms_parties(self):
        """ Tests if updating the shipping line name updates the partner's name in shipping line view. """
        partner = self.partner_model.create({
            'name': 'Old Line Name',
            'party_name': 'Line to Update',
        })

        context = {'is_cms_parties_view': True}
        vals = {'party_name': 'Updated Line Name'}

        partner.with_context(context).write(vals)
        self.assertEqual(partner.name, partner.party_name)
        self.assertEqual(partner.party_name, 'Updated Line Name')

    # def test_partner_gst_validation(self):
    #     """ Tests if the GST number validation works correctly. """
    #     # Test with incorrect GST length
    #     with self.assertRaises(ValidationError) as e:
    #         partner1 = self.partner_model.create({
    #             'name': 'Test Partner with GST',
    #             'gst_no': '1234'  # Invalid length
    #         })
    #         partner1.check_gst_details()
    #     self.assertEqual(e.exception.args[0], "GST Number entered should be 15 characters long. Please enter correct GST Number")
    #
    #     # Test with non-alphanumeric GST
    #     with self.assertRaises(ValidationError) as e:
    #         partner2 = self.partner_model.create({
    #             'name': 'Test Partner with GST1',
    #             'gst_no': '12345678901234!'  # Non-alphanumeric
    #         })
    #         partner2.check_gst_details()
    #     self.assertEqual(e.exception.args[0], "Please Enter Alphanumeric Value")
    #
    #     # Test with valid GST
    #     partner = self.partner_model.create({
    #         'name': 'Valid GST Partner',
    #         'gst_no': '123456789012345'  # Valid GST
    #     })
    #     self.assertEqual(partner.gst_no, '123456789012345')

    def test_check_line_status(self):
        """ Tests if the line status is computed correctly based on the 'active' field. """
        partner = self.partner_model.create({
            'name': 'Active Partner',
            'active': True
        })
        self.assertEqual(partner.line_status, 'active')
        partner.active = False
        partner._check_line_status()
        self.assertEqual(partner.line_status, 'inactive')

    def test_create_partner_with_create_info(self):
        """ Tests creation of partner with _get_create_record_info """
        user=self.env.user
        user.tz='UTC'
        partner=self.partner_model.create({
            'name':'New Partner',
            'shipping_line_name':'Test Shipping Line',
        })

        partner._get_create_record_info()
        self.assertTrue(partner.display_create_info)

    def test_modify_partner_with_modify_info(self):
        """ Tests modification of partner with _get_modify_record_info """
        user=self.env.user
        user.tz='UTC'
        partner=self.partner_model.create({
            'name':'Old Partner',
            'shipping_line_name':'Old Shipping Line',
        })
        partner.write({
            'shipping_line_name':'Updated Shipping Line',
        })
        partner._get_create_record_info()
        self.assertTrue(partner.display_modified_info)
