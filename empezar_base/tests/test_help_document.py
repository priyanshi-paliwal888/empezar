import base64
import os
from odoo.tests import common
from odoo.exceptions import ValidationError
from odoo.tools.misc import file_open


class TestHelpDocument(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Load a sample PDF file
        pdf_path = os.path.join(
            os.path.dirname(__file__), "attachment", "TestPDFfile.pdf"
        )
        with file_open(pdf_path, "rb") as f:
            file_content = base64.b64encode(f.read())

        # Create multiple help documents for different master menus
        cls.help_documents = {}
        created_menus = cls.env["help.document"].search([]).mapped("master_menu")
        for menu in (
            "shipping_lines",
            "container_facilities",
            "parties",
            "containers",
            "fiscal_years",
            "charges",
            "locations",
            "lolo_charge",
            "seal",
            "edi_settings",
            "user",
            "roles",
            "company",
        ):
            if menu not in created_menus:
                cls.help_documents[menu] = cls.env["help.document"].create(
                    {
                        "master_menu": menu,
                        "file": file_content,
                        "file_namex": f"{menu}_document.pdf",
                    }
                )

    def test_file_type_validation(self):
        """Test that only PDF files are allowed"""
        if self.env["help.document"].search([("master_menu", "=", "shipping_lines")]):
            shipping_doc = self.env["help.document"].search(
                [("master_menu", "=", "shipping_lines")], limit=1
            )
            shipping_doc.file_namex = "document.txt"
            shipping_doc.file = base64.b64encode(b"Some dummy content")
            with self.assertRaises(ValidationError, msg="Only Pdf files are allowed."):
                shipping_doc._check_file_type()

            shipping_doc.file_namex = "document.pdf"
            try:
                shipping_doc._check_file_type()
            except ValidationError:
                self.fail("ValidationError raised unexpectedly!")
        else:
            self.help_documents["shipping_lines"].file_namex = "document.txt"
            self.help_documents["shipping_lines"].file = base64.b64encode(
                b"Some dummy content"
            )
            with self.assertRaises(ValidationError, msg="Only Pdf files are allowed."):
                self.help_documents["shipping_lines"]._check_file_type()

            self.help_documents["shipping_lines"].file_namex = "document.pdf"
            try:
                self.help_documents["shipping_lines"]._check_file_type()
            except ValidationError:
                self.fail("ValidationError raised unexpectedly!")

    def test_master_menu_uniqueness(self):
        """Test that master_menu is unique"""
        if self.env["help.document"].search([("master_menu", "=", "shipping_lines")]):
            with self.assertRaises(ValidationError) as e:
                self.env["help.document"].create(
                    {
                        "master_menu": "shipping_lines",
                        "file": base64.b64encode(b"Some dummy content"),
                        "file_namex": "duplicate_document.pdf",
                    }
                )
            self.assertEqual(
                e.exception.args[0],
                "Help document records have already been created for shipping_lines.",
            )
        else:
            with self.assertRaises(
                ValidationError,
                msg="Help document records have already been created for shipping_lines.",
            ):
                self.env["help.document"].create(
                    {
                        "master_menu": "shipping_lines",
                        "file": base64.b64encode(b"Some dummy content"),
                        "file_namex": "duplicate_document.pdf",
                    }
                )

    def test_download_help_doc(self):
        """Test downloading help documents for each view"""

        view_mapping = {
            # 'shipping_lines': 'empezar_base.shipping_lines_tree_view',
            "container_facilities": "empezar_base.container_facilities_tree_view",
            "parties": "empezar_base.res_partner_parties_tree_view",
            "containers": "empezar_base.container_master_tree_view",
            "fiscal_years": "fiscal_year.view_account_fiscal_year_tree",
            "charges": "empezar_base.product_charge_template_tree_view",
            "locations": "empezar_base.res_company_location_tree_view",
            # 'lolo_charge': 'empezar_base.lolo_charge_tree_view',
            # 'seal': 'empezar_base.seal_management_tree_view',
            "edi_settings": "empezar_base.edi_settings_list_view",
            "user": "base.view_users_tree",
            "roles": "empezar_base.inherit_res_groups_tree_view",
            "company": "base.view_company_tree",
        }
        created_menus = self.env["help.document"].search([]).mapped("master_menu")
        for menu, view_ref in view_mapping.items():
            help_doc = self.help_documents[menu]
            view_id = self.env.ref(view_ref).id

            action = help_doc.download_help_doc(view_id=view_id)

            # self.assertEqual(
            #     action["type"], "ir.actions.act_url", f"Action type mismatch for {menu}"
            # )
            # self.assertIn(
            #     "download=true", action["url"], f"Download URL mismatch for {menu}"
            # )

            # attachment_id_str = action["url"].split("/")[-1].split("?")[0]
            # attachment_id = int(attachment_id_str)
            #
            # attachment = self.env["ir.attachment"].browse(attachment_id)
            # self.assertTrue(attachment.exists(), "Attachment should exist.")
            # self.assertEqual(
            #     attachment.name,
            #     help_doc.file_namex,
            #     "Attachment name should match the document file name.",
            # )
            # self.assertEqual(
            #     attachment.datas,
            #     help_doc.file,
            #     "Attachment content should match the document file content.",
            # )

    def test_download_help_doc_no_container(self):
        """Test when no help document exists for a given view_id"""
        created_menus = self.env["help.document"].search([]).mapped("master_menu")
        view_id = self.env.ref(
            "empezar_base.inherit_res_users_tree_view"
        ).id  # Assuming this view is not handled
        if self.env["help.document"].search([("master_menu", "=", "shipping_lines")]):
            action = (
                self.env["help.document"]
                .search([("master_menu", "=", "shipping_lines")])
                .download_help_doc(view_id=view_id)
            )
        else:
            action = self.help_documents["shipping_lines"].download_help_doc(
                view_id=view_id
            )

        self.assertIsNone(action, "Action should be None for unhandled view IDs.")
