from odoo.tests.common import TransactionCase


class TestLoloCharge(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env["res.company"].create(
            {
                "name": "Test Company",
                "parent_id": False,
            }
        )

        self.shipping_line = self.env["res.partner"].create(
            {
                "name": "Test Shipping Line",
                "is_shipping_line": True,
            }
        )

    def test_append_charges(self):
        """
        Test _append_charges method to ensure charges_for field is computed correctly.
        """
        lolo_charge = self.env["lolo.charge"].create(
            {
                "location": self.company.id,
                "shipping_line": self.shipping_line.id,
            }
        )

        lolo_charge.write(
            {
                "lolo_charge_lines": [(0, 0, {"container_size": "20ft"})],
            }
        )
        lolo_charge._append_charges()
        self.assertEqual(
            lolo_charge.charges_for, "20ft", "charges_for field should be '20ft'"
        )

    def test_download_xlsx_file(self):
        """
        Test download_xlsx_file method to ensure correct action is returned.
        """
        lolo_charge = self.env["lolo.charge"].create(
            {
                "location": self.company.id,
                "shipping_line": self.shipping_line.id,
            }
        )

        action = lolo_charge.download_xlsx_file()
        self.assertEqual(
            action["type"],
            "ir.actions.act_url",
            "Action type should be 'ir.actions.act_url'",
        )
        self.assertEqual(
            action["url"],
            "/empezar_base/static/src/reports/LoLoUploadSample.xlsx",
            "URL should match '/empezar_base/static/src/reports/LoLoUploadSample.xlsx'",
        )
        self.assertEqual(action["target"], "new", "Target should be 'new'")

    def test_get_create_record_info(self):
        """
        Test _get_create_record_info method to ensure display_create_info field is correctly set.
        """
        self.env.user.tz = "UTC"
        lolo_charge = self.env["lolo.charge"].create(
            {
                "location": self.company.id,
                "shipping_line": self.shipping_line.id,
            }
        )
        lolo_charge._get_create_record_info()
        self.assertTrue(
            lolo_charge.display_create_info,
            "display_create_info should match expected format",
        )

    def test_get_create_record_info_no_timezone(self):
        """
        Test _get_create_record_info method to ensure display_create_info field is correctly set.
        """
        self.env.user.tz = False
        lolo_charge = self.env["lolo.charge"].create(
            {
                "location": self.company.id,
                "shipping_line": self.shipping_line.id,
            }
        )
        lolo_charge._get_create_record_info()
        self.assertEqual(lolo_charge.display_create_info, "")

    def test_get_modify_record_info(self):
        """
        Test _get_modify_record_info method to ensure display_modified_info field is correctly set.
        """
        self.env.user.tz = "UTC"
        lolo_charge = self.env["lolo.charge"].create(
            {
                "location": self.company.id,
                "shipping_line": self.shipping_line.id,
            }
        )

        lolo_charge.write(
            {
                "shipping_line": False,
            }
        )
        lolo_charge._get_modify_record_info()
        self.assertTrue(
            lolo_charge.display_modified_info,
            "display_modified_info should match expected format",
        )

    def test_get_modify_record_info_no_timezone(self):
        """
        Test _get_modify_record_info method to ensure display_modified_info field is correctly set.
        """
        self.env.user.tz = False
        lolo_charge = self.env["lolo.charge"].create(
            {
                "location": self.company.id,
                "shipping_line": self.shipping_line.id,
            }
        )

        lolo_charge.write(
            {
                "shipping_line": False,
            }
        )
        lolo_charge._get_modify_record_info()
        self.assertEqual(lolo_charge.display_modified_info, "")
