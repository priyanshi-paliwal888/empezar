from odoo.tests.common import TransactionCase


class TestResPartner(TransactionCase):

    def test_default_get_with_context_importer(self):
        """Test default_get assigns parties_type_ids correctly when context is for importer"""
        partner_model = self.env["res.partner"]
        context = {"is_from_delivery": True, "is_from_importer": True}
        defaults = partner_model.with_context(context).default_get(["parties_type_ids"])

        expected_parties_type_id = self.env.ref("empezar_base.cms_parties_type_2").id
        self.assertIn("parties_type_ids", defaults)
        self.assertEqual(
            defaults["parties_type_ids"], [(6, 0, [expected_parties_type_id])]
        )

    def test_default_get_with_context_forwarder(self):
        """Test default_get assigns parties_type_ids correctly when context is for forwarder"""
        partner_model = self.env["res.partner"]
        context = {"is_from_delivery": True, "is_from_forwarder": True}
        defaults = partner_model.with_context(context).default_get(["parties_type_ids"])

        expected_parties_type_id = self.env.ref("empezar_base.cms_parties_type_4").id
        self.assertIn("parties_type_ids", defaults)
        self.assertEqual(
            defaults["parties_type_ids"], [(6, 0, [expected_parties_type_id])]
        )

    def test_default_get_with_context_booking_party(self):
        """Test default_get assigns parties_type_ids correctly when context is for booking party"""
        partner_model = self.env["res.partner"]
        context = {"is_from_delivery": True, "is_from_booking_party": True}
        defaults = partner_model.with_context(context).default_get(["parties_type_ids"])

        expected_parties_type_id = self.env.ref("empezar_base.cms_parties_type_12").id
        self.assertIn("parties_type_ids", defaults)
        self.assertEqual(
            defaults["parties_type_ids"], [(6, 0, [expected_parties_type_id])]
        )

    def test_default_get_with_context_exporter(self):
        """Test default_get assigns parties_type_ids correctly when context is for exporter"""
        partner_model = self.env["res.partner"]
        context = {"is_from_delivery": True, "is_from_exporter": True}
        defaults = partner_model.with_context(context).default_get(["parties_type_ids"])

        expected_parties_type_id = self.env.ref("empezar_base.cms_parties_type_1").id
        self.assertIn("parties_type_ids", defaults)
        self.assertEqual(
            defaults["parties_type_ids"], [(6, 0, [expected_parties_type_id])]
        )

    def test_create_with_context_importer(self):
        """Test create method assigns fields correctly when context is for importer"""
        context = {"is_from_delivery": True, "is_from_importer": True}
        vals = {"name": "Importer Partner"}
        partner = self.env["res.partner"].with_context(context).create(vals)

        expected_parties_type_id = self.env.ref("empezar_base.cms_parties_type_2").id
        expected_category_id = self.env.ref(
            "empezar_base.res_partner_cms_parties_tag_1"
        ).id

        self.assertTrue(partner.is_cms_parties)
        self.assertEqual(partner.name, "Importer Partner")
        self.assertEqual(partner.party_name, "Importer Partner")
        self.assertEqual(partner.category_id.ids, [expected_category_id])
        self.assertEqual(partner.parties_type_ids.ids, [expected_parties_type_id])

    def test_create_with_context_forwarder(self):
        """Test create method assigns fields correctly when context is for forwarder"""
        context = {"is_from_delivery": True, "is_from_forwarder": True}
        vals = {"name": "Forwarder Partner"}
        partner = self.env["res.partner"].with_context(context).create(vals)

        expected_parties_type_id = self.env.ref("empezar_base.cms_parties_type_4").id
        expected_category_id = self.env.ref(
            "empezar_base.res_partner_cms_parties_tag_1"
        ).id

        self.assertTrue(partner.is_cms_parties)
        self.assertEqual(partner.name, "Forwarder Partner")
        self.assertEqual(partner.party_name, "Forwarder Partner")
        self.assertEqual(partner.category_id.ids, [expected_category_id])
        self.assertEqual(partner.parties_type_ids.ids, [expected_parties_type_id])

    def test_create_with_context_booking_party(self):
        """Test create method assigns fields correctly when context is for booking party"""
        context = {"is_from_delivery": True, "is_from_booking_party": True}
        vals = {"name": "Booking Party Partner"}
        partner = self.env["res.partner"].with_context(context).create(vals)

        expected_parties_type_id = self.env.ref("empezar_base.cms_parties_type_12").id
        expected_category_id = self.env.ref(
            "empezar_base.res_partner_cms_parties_tag_1"
        ).id

        self.assertTrue(partner.is_cms_parties)
        self.assertEqual(partner.name, "Booking Party Partner")
        self.assertEqual(partner.party_name, "Booking Party Partner")
        self.assertEqual(partner.category_id.ids, [expected_category_id])
        self.assertEqual(partner.parties_type_ids.ids, [expected_parties_type_id])

    def test_create_with_context_exporter(self):
        """Test create method assigns fields correctly when context is for exporter"""
        context = {"is_from_delivery": True, "is_from_exporter": True}
        vals = {"name": "Exporter Partner"}
        partner = self.env["res.partner"].with_context(context).create(vals)

        expected_parties_type_id = self.env.ref("empezar_base.cms_parties_type_1").id
        expected_category_id = self.env.ref(
            "empezar_base.res_partner_cms_parties_tag_1"
        ).id

        self.assertTrue(partner.is_cms_parties)
        self.assertEqual(partner.name, "Exporter Partner")
        self.assertEqual(partner.party_name, "Exporter Partner")
        self.assertEqual(partner.category_id.ids, [expected_category_id])
        self.assertEqual(partner.parties_type_ids.ids, [expected_parties_type_id])
