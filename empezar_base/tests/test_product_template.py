# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestProductTemplate(TransactionCase):

    def setUp(self):
        super().setUp()
        self.product_template = self.env["product.template"]
        self.product_tag = self.env.ref("empezar_base.empezar_charge_product_tag")
        self.hsn_code = self.env["master.hsn.code"].create(
            {"name": "Test HSN Code", "code": "123456"}
        )
        self.user = self.env.user

    def test_create_chargeable_product(self):
        product = self.product_template.create(
            {
                "name": "Chargeable Product",
                "default_code": "CHG001",
                "is_chargeable_product": True,
                "gst_applicable": "yes",
                "hsn_code": self.hsn_code.id,
            }
        )
        self.assertTrue(product.is_chargeable_product)
        self.assertEqual(product.gst_applicable, "yes")
        self.assertEqual(product.hsn_code, self.hsn_code)

    def test_create_chargeable_product_with_gst_applicable_yes(self):
        vals = {
            "charge_name": "Test Chargeable Product",
            "charge_code": "TC001",
            "name": "Test Chargeable Product",
            "is_chargeable_product": True,
            "gst_applicable": "yes",
            "gst_rate": [],
            "hsn_code": self.hsn_code.id,
            "company_id": self.env.user.company_id.id,
        }
        product = self.product_template.with_context(
            is_charge_product_view=True
        ).create(vals)
        self.assertEqual(product.name, vals["charge_name"])
        self.assertEqual(product.default_code, vals["charge_code"])
        self.assertTrue(product.is_chargeable_product)
        self.assertIn(self.product_tag.id, product.product_tag_ids.ids)
        self.assertEqual(product.detailed_type, "service")
        self.assertEqual(product.company_id, self.env.user.company_id)
        self.assertEqual(product.hsn_code, self.hsn_code)
        # self.assertEqual(product.taxes_id, vals['gst_rate'])

    def test_duplicate_name_code(self):
        product1 = self.product_template.create(
            {
                "name": "Duplicate Product",
                "charge_name": "Duplicate Product",
                "default_code": "DUP001",
                "charge_code": "DUP001",
                "is_chargeable_product": True,
                "gst_applicable": "yes",
                "hsn_code": self.hsn_code.id,
            }
        )
        with self.assertRaises(ValidationError):
            self.product_template.create(
                {
                    "name": "Duplicate Product",
                    "charge_name": "Duplicate Product",
                    "default_code": "DUP002",
                    "charge_code": "DUP002",
                    "is_chargeable_product": True,
                    "gst_applicable": "yes",
                    "hsn_code": self.hsn_code.id,
                }
            )
        with self.assertRaises(ValidationError):
            self.product_template.create(
                {
                    "name": "Unique Product",
                    "charge_name": "Unique Product",
                    "default_code": "DUP001",
                    "charge_code": "DUP001",
                    "is_chargeable_product": True,
                    "gst_applicable": "yes",
                    "hsn_code": self.hsn_code.id,
                }
            )

    def test_invoice_type_constraint(self):

        lift_on = self.product_template.search(
            [("invoice_type", "=", "lift_on")], limit=1
        )
        if not lift_on:
            product1 = self.product_template.create(
                {
                    "name": "Lift On Product",
                    "default_code": "LON001",
                    "is_chargeable_product": True,
                    "gst_applicable": "yes",
                    "invoice_type": "lift_on",
                    "hsn_code": self.hsn_code.id,
                }
            )
            with self.assertRaises(ValidationError):
                self.product_template.create(
                    {
                        "name": "Another Lift On Product",
                        "default_code": "LON002",
                        "is_chargeable_product": True,
                        "gst_applicable": "yes",
                        "invoice_type": "lift_on",
                        "hsn_code": self.hsn_code.id,
                    }
                )
        lift_off = self.product_template.search(
            [("invoice_type", "=", "lift_off")], limit=1
        )
        if not lift_off:
            product2 = self.product_template.create(
                {
                    "name": "Lift On Product",
                    "default_code": "LON001",
                    "is_chargeable_product": True,
                    "gst_applicable": "yes",
                    "invoice_type": "lift_off",
                    "hsn_code": self.hsn_code.id,
                }
            )
            with self.assertRaises(ValidationError):
                self.product_template.create(
                    {
                        "name": "Another Lift Off Product",
                        "default_code": "LON003",
                        "is_chargeable_product": True,
                        "gst_applicable": "yes",
                        "invoice_type": "lift_off",
                        "hsn_code": self.hsn_code.id,
                    }
                )

    def test_create_record_info_with_timezone(self):
        self.user.tz = "UTC"
        product = self.product_template.create(
            {
                "name": "Product with Info",
                "default_code": "INF001",
                "is_chargeable_product": True,
                "gst_applicable": "yes",
                "hsn_code": self.hsn_code.id,
            }
        )
        product._get_create_record_info()
        self.assertTrue(product.display_create_info)

    def test_create_record_info_without_timezone(self):
        self.user.tz = False
        product = self.product_template.create(
            {
                "name": "Product with Info",
                "default_code": "INF001",
                "is_chargeable_product": True,
                "gst_applicable": "yes",
                "hsn_code": self.hsn_code.id,
            }
        )
        product._get_create_record_info()
        self.assertEqual(product.display_create_info, "")

    def test_modify_record_info_with_timezone(self):
        self.user.tz = "UTC"
        product = self.product_template.create(
            {
                "name": "Product with Info",
                "default_code": "INF001",
                "is_chargeable_product": True,
                "gst_applicable": "yes",
                "hsn_code": self.hsn_code.id,
            }
        )
        product.write({"name": "Updated Product with Info"})
        product._get_modify_record_info()
        self.assertTrue(product.display_modified_info)

    def test_modify_record_info_without_timezone(self):
        self.user.tz = False
        product = self.product_template.create(
            {
                "name": "Product with Info",
                "default_code": "INF001",
                "is_chargeable_product": True,
                "gst_applicable": "yes",
                "hsn_code": self.hsn_code.id,
            }
        )
        product.write({"name": "Updated Product with Info"})
        product._get_modify_record_info()
        self.assertEqual(product.display_modified_info, "")

    def test_write_with_gst_applicable_no(self):
        product = self.product_template.create(
            {
                "name": "GST Product",
                "default_code": "GSP001",
                "is_chargeable_product": True,
                "gst_applicable": "yes",
                "hsn_code": self.hsn_code.id,
            }
        )
        product.write({"gst_applicable": "no"})
        self.assertFalse(product.hsn_code)
        self.assertFalse(product.taxes_id)

    def test_clear_taxes_id_when_gst_applicable_no(self):
        product = self.product_template.create(
            {
                "name": "Test Product",
                "default_code": "TST001",
                "is_chargeable_product": True,
                "gst_applicable": "no",
                "hsn_code": self.hsn_code.id,
                "gst_rate": [(6, 0, [1, 2, 3])],  # Assuming some tax ids
            }
        )
        product._clear_taxes_id()
        self.assertFalse(product.gst_rate)
        self.assertFalse(product.hsn_code)
