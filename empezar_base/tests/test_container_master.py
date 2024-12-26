from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestContainerMaster(TransactionCase):

    def setUp(self):
        super().setUp()
        self.container_model = self.env["container.master"]
        self.partner_model = self.env["res.partner"]
        self.container_type_data_model = self.env["container.type.data"]

        # Create a sample container type data record
        self.container_type_data_1 = self.container_type_data_model.create(
            {
                "name": "20ft Standard",
                "type_group_code": "STD",
                "company_size_type_code": "20ST",
                "te_us": 1.0,
                "order_number": 1,
                "is_refer": "no",
                "size": "20ft",
                "is_containerized_product": True,
                "active": True,
            }
        )

    def test_create_container(self):
        container_data = {
            "name": "GVTU3000389",
            "shipping_line_id": self.partner_model.create(
                {"name": "Test Shipping Line", "is_shipping_line": True}
            ).id,
            "type_size": self.container_type_data_1.id,
            "production_month_year": "2024-06-01",
            "gross_wt": 5000,
            "tare_wt": 3000,
        }
        container = self.container_model.create(container_data)
        self.assertTrue(container)

    def test_weight_validation(self):
        container_data = {
            "name": "GVTU3000389",
            "shipping_line_id": self.partner_model.create(
                {"name": "Test Shipping Line", "is_shipping_line": True}
            ).id,
            "type_size": self.container_type_data_1.id,
            "production_month_year": "2024-06-01",
            "gross_wt": 3000,
            "tare_wt": 4000,  # Tare weight greater than gross weight
        }
        with self.assertRaises(ValidationError):
            self.container_model.create(container_data)

        container_data["tare_wt"] = 0
        with self.assertRaises(ValidationError):
            self.container_model.create(container_data)

        container_data["tare_wt"] = 4000
        container_data["gross_wt"] = 0
        with self.assertRaises(ValidationError):
            self.container_model.create(container_data)

    def test_compute_date_field(self):
        container = self.container_model.create(
            {
                "name": "EUJU1234567",
                "shipping_line_id": self.partner_model.create(
                    {"name": "Test Shipping Line", "is_shipping_line": True}
                ).id,
                "type_size": self.container_type_data_1.id,
                "month": "06",
                "year": "2024",
                "gross_wt": 5000,
                "tare_wt": 3000,
            }
        )
        container._compute_date_field()  # Manually invoke to test
        self.assertEqual(container.production_month_year, "06/2024")

    def test_compute_date_field_no_month_year(self):
        container = self.container_model.create(
            {
                "name": "EUJU1234567",
                "shipping_line_id": self.partner_model.create(
                    {"name": "Test Shipping Line", "is_shipping_line": True}
                ).id,
                "type_size": self.container_type_data_1.id,
                "gross_wt": 5000,
                "tare_wt": 3000,
            }
        )
        container._compute_date_field()  # Manually invoke to test
        self.assertFalse(container.production_month_year)

    def test_create_record_info(self):
        self.env.user.tz = "UTC"
        container = self.container_model.create(
            {
                "name": "EUJU1234567",
                "shipping_line_id": self.partner_model.create(
                    {"name": "Test Shipping Line", "is_shipping_line": True}
                ).id,
                "type_size": self.container_type_data_1.id,
                "gross_wt": 5000,
                "tare_wt": 3000,
            }
        )
        container._get_create_record_info()  # Manually invoke to test
        self.assertTrue(container.display_create_info)  # Expecting non-empty string

    #

    def test_create_record_info_without_timezone(self):
        self.env.user.tz = False
        container = self.container_model.create(
            {
                "name": "EUJU1234567",
                "shipping_line_id": self.partner_model.create(
                    {"name": "Test Shipping Line", "is_shipping_line": True}
                ).id,
                "type_size": self.container_type_data_1.id,
                "gross_wt": 5000,
                "tare_wt": 3000,
            }
        )
        container._get_create_record_info()  # Manually invoke to test
        self.assertEqual(container.display_create_info, "")

    def test_modify_record_info(self):
        self.env.user.tz = "UTC"
        container = self.container_model.create(
            {
                "name": "EUJU1234567",
                "shipping_line_id": self.partner_model.create(
                    {"name": "Test Shipping Line", "is_shipping_line": True}
                ).id,
                "type_size": self.container_type_data_1.id,
                "gross_wt": 5000,
                "tare_wt": 3000,
            }
        )
        container.gross_wt = 6000
        container._get_modify_record_info()  # Manually invoke to test
        self.assertTrue(container.display_modified_info)  # Expecting non-empty string

    def test_modify_record_info_without_timezone(self):
        self.env.user.tz = False
        container = self.container_model.create(
            {
                "name": "FUJU1234568",
                "shipping_line_id": self.partner_model.create(
                    {"name": "Test Shipping Line", "is_shipping_line": True}
                ).id,
                "type_size": self.container_type_data_1.id,
                "gross_wt": 5000,
                "tare_wt": 3000,
            }
        )
        container.gross_wt = 6000
        container._get_modify_record_info()  # Manually invoke to test
        self.assertEqual(container.display_modified_info, "")

    def test_create_with_import_context(self):
        container_data = {
            "name": "EUJU1234567",
            "shipping_line_id": self.partner_model.create(
                {"name": "Test Shipping Line", "is_shipping_line": True}
            ).id,
            "type_size": self.container_type_data_1.id,
            "gross_wt": 5000,
            "tare_wt": 3000,
        }
        container = self.container_model.with_context(import_file=True).create(
            container_data
        )
        self.assertTrue(container.is_import)

    def test_compute_display_sources_import(self):
        container = self.container_model.create(
            {
                "name": "EUJU1234567",
                "shipping_line_id": self.partner_model.create(
                    {"name": "Test Shipping Line", "is_shipping_line": True}
                ).id,
                "type_size": self.container_type_data_1.id,
                "gross_wt": 5000,
                "tare_wt": 3000,
                "is_import": True,  # Set is_import to True
            }
        )
        self.assertEqual(container.display_sources, "Excel")

    def test_compute_display_sources_not_import(self):
        container = self.container_model.create(
            {
                "name": "EUJU1234567",
                "shipping_line_id": self.partner_model.create(
                    {"name": "Test Shipping Line", "is_shipping_line": True}
                ).id,
                "type_size": self.container_type_data_1.id,
                "gross_wt": 5000,
                "tare_wt": 3000,
                "is_import": False,  # Set is_import to False
            }
        )
        self.assertEqual(container.display_sources, "System")
