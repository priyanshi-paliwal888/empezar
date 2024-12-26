import logging
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestContainerTypeEdi(TransactionCase):

    def setUp(self):
        super().setUp()
        self.container_type_data_model = self.env["container.type.data"]
        self.container_type_edi_model = self.env["container.type.edi"]
        self.partner_model = self.env["res.partner"]

        # Create a sample partner
        self.partner = self.partner_model.create(
            {"name": "Sample Partner", "is_shipping_line": True}
        )

        # Create a sample container type data
        self.container_type_data = self.container_type_data_model.create(
            {"name": "20ft Standard", "company_size_type_code": "20ST"}
        )

        self.inactive_container_type_data = self.container_type_data_model.create(
            {
                "name": "Inactive Container",
                "company_size_type_code": "INACT",
                "active": False,
            }
        )

    def test_create_container_type_edi(self):
        container_type_edi = self.container_type_edi_model.create(
            {
                "container_type_data_id": self.container_type_data.id,
                "edi_code": "E001",
                "partner_id": self.partner.id,
            }
        )

        self.assertEqual(container_type_edi.name, self.container_type_data.name)
        self.assertEqual(
            container_type_edi.type_group_code,
            self.container_type_data.company_size_type_code,
        )

    def test_check_active_records(self):
        container_type_edi = self.container_type_edi_model.create(
            {
                "container_type_data_id": self.container_type_data.id,
                "edi_code": "E003",
                "partner_id": self.partner.id,
                "active": True,
            }
        )

        container_type_edi.check_active_records()
        self.assertEqual(container_type_edi.rec_status, "active")

        container_type_edi.write({"active": False})
        container_type_edi.check_active_records()
        self.assertEqual(container_type_edi.rec_status, "disable")

    def test_create_record_info(self):
        self.env.user.tz = "UTC"
        container_type_edi = self.container_type_edi_model.create(
            {
                "container_type_data_id": self.container_type_data.id,
                "edi_code": "E004",
                "partner_id": self.partner.id,
            }
        )
        container_type_edi._get_create_record_info()
        _logger.info(f"display_create_info: {container_type_edi.display_create_info}")
        self.assertTrue(container_type_edi.display_create_info)

    def test_create_record_info_no_timezone(self):
        self.env.user.tz = False
        container_type_edi = self.container_type_edi_model.create(
            {
                "container_type_data_id": self.container_type_data.id,
                "edi_code": "E004",
                "partner_id": self.partner.id,
            }
        )
        container_type_edi._get_create_record_info()
        _logger.info(f"display_create_info: {container_type_edi.display_create_info}")
        self.assertEqual(container_type_edi.display_create_info, "")

    def test_modify_record_info(self):
        self.env.user.tz = "UTC"
        container_type_edi = self.container_type_edi_model.create(
            {
                "container_type_data_id": self.container_type_data.id,
                "edi_code": "E005",
                "partner_id": self.partner.id,
            }
        )
        container_type_edi.write({"edi_code": "E006"})
        container_type_edi._get_modify_record_info()
        self.assertTrue(container_type_edi.display_modified_info)

    def test_modify_record_info_no_timezone(self):
        self.env.user.tz = False
        container_type_edi = self.container_type_edi_model.create(
            {
                "container_type_data_id": self.container_type_data.id,
                "edi_code": "E005",
                "partner_id": self.partner.id,
            }
        )
        container_type_edi.write({"edi_code": "E006"})
        container_type_edi._get_modify_record_info()
        self.assertEqual(container_type_edi.display_modified_info, "")

    def test_onchange_container_type_data_id_active(self):
        """
        Test _onchange_container_type_data_id when the selected container type data is active.
        """
        container_type_edi = self.container_type_edi_model.create(
            {
                "container_type_data_id": self.container_type_data.id,
                "edi_code": "E001",
                "partner_id": self.partner.id,
            }
        )

        # This should not raise any validation error
        container_type_edi._onchange_container_type_data_id()

    def test_onchange_container_type_data_id_inactive(self):
        """
        Test _onchange_container_type_data_id when the selected container type data is inactive.
        It should raise a ValidationError.
        """
        container_type_edi = self.container_type_edi_model.create(
            {
                "container_type_data_id": self.inactive_container_type_data.id,
                "edi_code": "E002",
                "partner_id": self.partner.id,
            }
        )

        with self.assertRaises(
            ValidationError, msg="Please Select Active Container Name."
        ):
            container_type_edi._onchange_container_type_data_id()
