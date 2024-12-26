from odoo.tests.common import TransactionCase


class TestMasterHSNSACCode(TransactionCase):

    def setUp(self):
        super().setUp()
        self.hsn_code_model = self.env["master.hsn.code"]

    def test_compute_display_name(self):
        # Create a new HSN/SAC code record
        hsn_code = self.hsn_code_model.create(
            {"name": "Service Tax", "code": 1234, "active": True}
        )
        hsn_code._compute_display_name()
        expected_display_name = "1234 (Service Tax)"
        self.assertEqual(hsn_code.display_name, expected_display_name)

        hsn_code2 = self.hsn_code_model.create(
            {"name": "Goods Tax", "code": 5678, "active": True}
        )
        hsn_code2._compute_display_name()
        expected_display_name2 = "5678 (Goods Tax)"
        self.assertEqual(hsn_code2.display_name, expected_display_name2)
