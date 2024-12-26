from odoo.tests import common
from odoo.exceptions import ValidationError


class TestContainerInventory(common.TransactionCase):

    def setUp(self):
        super().setUp()

        self.test_company = self.env["res.company"].create(
            {
                "name": "Test Company",
            }
        )

        self.shipping_line = self.env["res.partner"].create(
            {
                "name": "Test Shipping Line",
                "company_id": self.test_company.id,
            }
        )

        self.ContainerInventory = self.env["container.inventory"]
        self.container_type_size = self.env["container.type.data"].create(
            {
                "name": "20FT",
                "company_size_type_code": "20FT",
                "is_refer": "no",
            }
        )

        self.container_master = self.env["container.master"].create(
            {
                "name": "GVTU3000389",
                "type_size": self.container_type_size.id,
                "shipping_line_id": self.shipping_line.id,
                "gross_wt": "123",
                "tare_wt": "123",
            }
        )

        self.damage_condition = self.env["damage.condition"].create(
            {"name": "Damage A", "damage_code": "Size/Type A", "active": True}
        )

    def test_container_number_valid(self):
        """Test for valid container number"""
        container = self.ContainerInventory.create(
            {
                "name": "GVTU3000389",
                "container_master_id": self.container_master.id,
                "damage_condition": self.damage_condition.id,
            }
        )
        self.assertEqual(container.name, "GVTU3000389")

    def test_container_number_invalid(self):
        """Test for invalid container number format"""
        with self.assertRaises(ValidationError):
            self.ContainerInventory.create(
                {
                    "name": "INVALID123",
                    "container_master_id": self.container_master.id,
                    "damage_condition": self.damage_condition.id,
                }
            )

    def test_check_digit_valid(self):
        """Test for valid check digit"""
        container = self.ContainerInventory.create(
            {
                "name": "GVTU3000389",  # Assuming 7 is the correct check digit
                "container_master_id": self.container_master.id,
                "damage_condition": self.damage_condition.id,
            }
        )
        self.assertEqual(container.name, "GVTU3000389")

    def test_create_record_import(self):
        """Test record creation with import flag"""
        container = self.ContainerInventory.with_context(import_file=True).create(
            {
                "name": "FUJU1234568",
                "container_master_id": self.container_master.id,
                "damage_condition": self.damage_condition.id,
            }
        )
        self.assertTrue(container.is_import)
        self.assertEqual(container.display_sources, "Excel")

    def test_create_record_system(self):
        """Test record creation without import flag"""
        container = self.ContainerInventory.create(
            {
                "name": "FUJU1234568",
                "container_master_id": self.container_master.id,
                "damage_condition": self.damage_condition.id,
            }
        )
        self.assertFalse(container.is_import)
        self.assertEqual(container.display_sources, "System")

    def test_create_log_display(self):
        """Test if creation log is displayed correctly"""
        container = self.ContainerInventory.create(
            {
                "name": "FUJU1234568",
                "container_master_id": self.container_master.id,
                "damage_condition": self.damage_condition.id,
            }
        )
        self.assertTrue(container.display_create_info)

    def test_modify_log_display(self):
        """Test if modification log is displayed correctly"""
        container = self.ContainerInventory.create(
            {
                "name": "FUJU1234568",
                "container_master_id": self.container_master.id,
                "damage_condition": self.damage_condition.id,
            }
        )
        container.write({"name": "GVTU3000389"})
        self.assertTrue(container.display_modified_info)
