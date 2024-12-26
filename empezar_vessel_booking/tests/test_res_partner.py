# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestResPartner(TransactionCase):

    def setUp(self):
        super(TestResPartner, self).setUp()
        self.transporter_type = self.env.ref('empezar_base.cms_parties_type_5')
        self.cms_parties_tag = self.env.ref('empezar_base.res_partner_cms_parties_tag_1')
        self.company = self.env.user.company_id

    def test_default_get_with_context(self):
        context = dict(self.env.context, is_from_booking=True)
        res = self.env['res.partner'].with_context(context).default_get(['parties_type_ids'])
        expected_ids = [(6, 0, [self.transporter_type.id])]
        self.assertEqual(res.get('parties_type_ids'), expected_ids)

    def test_create_with_context(self):
        context = dict(self.env.context, is_from_booking=True)
        partner = self.env['res.partner'].with_context(context).create({
            'name': 'Test Partner',
        })
        self.assertTrue(partner.is_cms_parties)
        self.assertEqual(partner.name, 'Test Partner')
        self.assertEqual(partner.party_name, 'Test Partner')
        self.assertIn(self.cms_parties_tag.id, partner.category_id.ids)
        self.assertIn(self.transporter_type.id, partner.parties_type_ids.ids)

    def test_write_with_context(self):
        partner = self.env['res.partner'].create({
            'name': 'Old Name',
            'party_name': 'New Name',
        })
        context = dict(self.env.context, is_from_booking=True)
        partner.with_context(context).write({'party_name': 'Updated Name'})
        updated_partner = self.env['res.partner'].browse(partner.id)
        self.assertEqual(updated_partner.name, 'Updated Name')

    def test_create_without_context(self):
        partner = self.env['res.partner'].create({
            'name': 'Regular Partner',
        })
        self.assertFalse(partner.is_cms_parties)
        self.assertEqual(partner.name, 'Regular Partner')
        self.assertNotEqual(partner.party_name, 'Regular Partner')
        self.assertNotIn(self.cms_parties_tag.id, partner.category_id.ids)
        self.assertNotIn(self.transporter_type.id, partner.parties_type_ids.ids)

    def test_write_without_context(self):
        partner = self.env['res.partner'].create({
            'name': 'Initial Name',
        })
        partner.write({'name': 'New Name'})
        updated_partner = self.env['res.partner'].browse(partner.id)
        self.assertEqual(updated_partner.name, 'New Name')
