from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from openpyxl import Workbook
import base64
import io


class TestEnableProfilingWizard(TransactionCase):

    def setUp(self):
        super().setUp()
        self.shipping_line = self.env['res.partner'].create({
            'name': 'Test Shipping Line',
            'is_shipping_line': True,
        })
        self.location_company = self.env['res.company'].create({
            'name': 'Test Company',
            'parent_id': False,
        })
        self.wizard = self.env['bulk.import.wizard'].create({
            'shipping_line': self.shipping_line.id,
        })

    def create_excel_file(self, data):
        """
        Helper method to create an Excel file from data.
        """
        wb = Workbook()
        ws = wb.active
        for row in data:
            ws.append(row)
        file_data = io.BytesIO()
        wb.save(file_data)
        file_data.seek(0)
        return file_data.read()

    def test_action_import_valid_data(self):
        """
        Test the action_import method with valid data.
        """
        data = [
            ['Location Name (Code)', 'Lift OFF', None, None, None, 'Lift ON', None, None, None],
            [None, '20 FT', '20 FT Reefer', '40 FT', '40 FT Reefer', '20 FT', '20 FT Reefer', '40 FT', '40 FT Reefer'],
            ['Test Company', 1, 2, 3, 4, 5, 6, 7, 8],
        ]
        file_content = self.create_excel_file(data)
        self.wizard.file_namex = 'test_file.xlsx'
        self.wizard.file = base64.b64encode(file_content)
        self.wizard.action_import()

        location_id = self.location_company.id
        lolo_charges = self.env['lolo.charge'].search([('location', '=', location_id)])
        self.assertTrue(lolo_charges, "Lolo Charge records should have been created")
        self.assertEqual(lolo_charges.shipping_line.id, self.shipping_line.id, "The shipping line should match")

        self.assertTrue(self.wizard.is_import_done, "Import should be marked as done")
        self.assertEqual(len(self.wizard.listA), 1, "One record should have been created")

    def test_action_import_invalid_header(self):
        """
        Test the action_import method with invalid headers in the Excel file.
        """
        data = [
            ['LocationInvalid', '20ft Lift Off 1', '20ft Lift Off 2', '20ft Lift Off 3', '20ft Lift Off 4',
             '20ft Lift On 1', '20ft Lift On 2', '20ft Lift On 3', '20ft Lift On 4'],
            [],
            ['Invalid Location', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'],
        ]
        file_content = self.create_excel_file(data)
        self.wizard.file_namex = 'test_file_invalid_header.xlsx'
        self.wizard.file = base64.b64encode(file_content)

        with self.assertRaises(ValidationError) as e:
            self.wizard.action_import()
        self.assertEqual(str(e.exception), "Invalid columns headers in the file uploaded.")

    def test_action_import_invalid_data(self):
        """
        Test the action_import method with invalid data (non-numeric values).
        """
        data = [
            ['Location Name (Code)', 'Lift OFF', None, None, None, 'Lift ON', None, None, None],
            [None, '20 FT', '20 FT Reefer', '40 FT', '40 FT Reefer', '20 FT', '20 FT Reefer', '40 FT', '40 FT Reefer'],
            ['Test Company', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        ]
        file_content = self.create_excel_file(data)
        self.wizard.file_namex = 'test_file_invalid_data.xlsx'
        self.wizard.file = base64.b64encode(file_content)
        self.wizard.action_import()
        self.assertIn(3, self.wizard.listC, "Row 3 should be marked as having invalid numeric values")
        self.assertTrue(self.wizard.hide_numeric_values, "The numeric values error flag should be set")

    def test_action_import_invalid_location(self):
        """
        Test the action_import method with a non-existing location.
        """
        data = [
            ['Location Name (Code)', 'Lift OFF', None, None, None, 'Lift ON', None, None, None],
            [None, '20 FT', '20 FT Reefer', '40 FT', '40 FT Reefer', '20 FT', '20 FT Reefer', '40 FT', '40 FT Reefer'],
            ['Invalid Location', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'],
        ]
        file_content = self.create_excel_file(data)
        self.wizard.file_namex = 'test_file_invalid_location.xlsx'
        self.wizard.file = base64.b64encode(file_content)
        self.wizard.action_import()

        self.assertIn(3, self.wizard.listB, "Row 3 should be marked as having an invalid location")
        self.assertTrue(self.wizard.hide_invalid_location, "The invalid location error flag should be set")
