from odoo.tests.common import TransactionCase


class TestContainerTypeData(TransactionCase):

    def setUp(self):
        super().setUp()
        self.container_type_data_model = self.env["container.type.data"]

    def test_compute_display_name_with_code(self):
        # Create a record with both name and company_size_type_code
        container_type_data = {
            "name": "20ft Standard",
            "company_size_type_code": "20ST",
        }
        container_type = self.container_type_data_model.create(container_type_data)
        container_type._compute_display_name()
        expected_display_name = "20ft Standard (20ST)"
        self.assertEqual(container_type.display_name, expected_display_name)

    def test_compute_display_name_without_code(self):
        # Create a record with only name
        container_type_data = {
            "name": "20ft Standard",
            "company_size_type_code": False,
        }
        container_type = self.container_type_data_model.create(container_type_data)
        container_type._compute_display_name()
        expected_display_name = "20ft Standard"
        self.assertEqual(container_type.display_name, expected_display_name)

    def test_compute_display_name_update_code(self):
        container_type_data = {
            "name": "20ft Standard",
        }
        container_type = self.container_type_data_model.create(container_type_data)
        container_type._compute_display_name()
        self.assertEqual(container_type.display_name, "20ft Standard")
        container_type.write({"company_size_type_code": "20ST"})
        container_type._compute_display_name()
        expected_display_name = "20ft Standard (20ST)"
        self.assertEqual(container_type.display_name, expected_display_name)
