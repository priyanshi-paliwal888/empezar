from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import openpyxl
import io
import base64
import re


class EnableProfilingWizard(models.TransientModel):
    _name = 'bulk.import.wizard'
    _description = "Upload Lolo Charges"

    shipping_line = fields.Many2one('res.partner', string="Shipping Line", domain="[('is_shipping_line', '=', True)]")
    file = fields.Binary('Upload LOLO Charges')
    file_namex = fields.Char('Binary Name')
    delimiter = fields.Char('Delimiter', default=',')
    my_flie = fields.Char('name')

    created_record = fields.Text('Created Record :', readonly=True)
    invalid_location = fields.Text('Invalid Location Details on these rows :', readonly=True)
    numeric_values = fields.Text('Only numeric values are accepted for Lift ON or Lift OFF on these rows :', readonly=True)
    updated_record = fields.Text('Updated Record on these rows :', readonly=True)
    hide_invalid_location = fields.Boolean(default=True)
    hide_numeric_values = fields.Boolean(default=True)
    hide_updated_record = fields.Boolean(default=True)
    is_import_done = fields.Boolean(default=False)
    is_download = fields.Boolean(default=False)

    listA = []
    listB = []
    listC = []
    listD = []
    @api.onchange('file')
    @api.constrains('file')
    def _check_file_type(self):
        """
            This method validates the uploaded shipping logo:

            **Raises:**
                ValidationError:
                ->If the uploaded file is not .xls/.xlsx
                ->If the uploaded logo size exceeds 1MB.
        """
        if self.file:
            # Get the file name and check the extension
            file_name = self.file_namex
            if not file_name.lower().endswith(('.xls', '.xlsx')):
                raise ValidationError("File Type selected is not allowed. Please upload files of types - .xls / .xlsx.")
            if len(self.file) > 5 * 1024 * 1024:
                raise ValidationError("File size cannot exceed 5MB.")

    def action_import(self):
        count = 2

        # Read data from the uploaded Excel file
        file_data = io.BytesIO(base64.b64decode(self.file))
        wb = openpyxl.load_workbook(file_data)
        sheet = wb.active  # Assuming data is in the first sheet

        # Validate column headers
        expected_headers = ['Location Name (Code)', 'Lift OFF', None, None, None, 'Lift ON', None, None, None, None,
                            '20 FT', '20 FT Reefer', '40 FT', '40 FT Reefer', '20 FT', '20 FT Reefer', '40 FT',
                            '40 FT Reefer']
        actual_header1 = [cell.value for cell in sheet[1]]
        actual_header2 = [cell.value for cell in sheet[2]]
        actual_headers = actual_header1 + actual_header2

        if actual_headers != expected_headers:
            raise ValidationError("Invalid columns headers in the file uploaded.")

        charge_lines = []

        # Iterate through rows and create customer records
        for row in sheet.iter_rows(min_row=3, values_only=True):  # Skip header row if present
            count += 1
            try:
                location = row[0]
                lift_off_20ft1 = row[1]
                lift_off_20ft2 = row[2]
                lift_off_20ft3 = row[3]
                lift_off_20ft4 = row[4]
                lift_on_20ft1 = row[5]
                lift_on_20ft2 = row[6]
                lift_on_20ft3 = row[7]
                lift_on_20ft4 = row[8]
            except IndexError:
                raise ValidationError(f"Invalid data format in row {count + 1}")

            if isinstance(location, str):
                # Use regular expression to remove the code inside parentheses
                location_name = re.sub(r'\s?\(.*\)', '', location).strip()
            else:
                location_name = location  # You can handle the case where location is not a string, if needed

            allowed_values = ['20ft', '20ft_reefer', '40ft', '40ft_reefer']
            location_id = self.env['res.company'].search([('name', '=', location_name)]).id
            value = [lift_off_20ft1, lift_off_20ft2, lift_off_20ft3, lift_off_20ft4, lift_on_20ft1,
                     lift_on_20ft2, lift_on_20ft3, lift_on_20ft4]

            if not location_id:
                self.listB.append(count)
            elif not all(isinstance(val, int) for val in value) and all((vals != None) for vals in value):
                self.listC.append(count)
            else:
                for i in allowed_values:
                    if i == '20ft':
                        charge_lines.append((0, 0, {
                            'container_size': i,
                            'lift_on': lift_on_20ft1,
                            'lift_off': lift_off_20ft1,
                        }))
                    elif i == '20ft_reefer':
                        charge_lines.append((0, 0, {
                            'container_size': i,
                            'lift_on': lift_on_20ft2,
                            'lift_off': lift_off_20ft2,
                        }))
                    elif i == '40ft':
                        charge_lines.append((0, 0, {
                            'container_size': i,
                            'lift_on': lift_on_20ft3,
                            'lift_off': lift_off_20ft3,
                        }))
                    elif i == '40ft_reefer':
                        charge_lines.append((0, 0, {
                            'container_size': i,
                            'lift_on': lift_on_20ft4,
                            'lift_off': lift_off_20ft4,
                        }))

                # Create the lolo charge record with the updated charge lines
                lolo_charge = self.env['lolo.charge'].search([('location', '=', location_id)])
                if lolo_charge:
                    lolo_charge.write({
                        'shipping_line': self.shipping_line.id,
                        'lolo_charge_lines': [(5, 0, 0)] + charge_lines
                    })
                    self.listD.append(count)
                else:
                    # Create the new lolo charge record with charge lines
                    self.env['lolo.charge'].create({
                        'shipping_line': self.shipping_line.id,
                        'location': location_id,
                        'lolo_charge_lines': charge_lines,
                    })
                    self.listA.append(count)
                charge_lines.clear()

        created_record = len(self.listA)
        invalid_location = f"{self.listB}"
        numeric_values = f"{self.listC}"
        updated_record = f"{self.listD}"

        if not self.listB:
            self.hide_invalid_location = False
        if not self.listC:
            self.hide_numeric_values = False
        if not self.listD:
            self.hide_updated_record = False
        else:
            pass

        self.is_import_done = True
        self.created_record = created_record
        self.invalid_location = invalid_location
        self.numeric_values = numeric_values
        self.updated_record = updated_record

        return {
            'name': 'Upload LOLO Charges',
            'view_mode': 'form',
            'view_id': self.env.ref('empezar_base.bulk_import_form').id,
            'res_model': 'bulk.import.wizard',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def action_close(self):
        self.listA.clear()
        self.listB.clear()
        self.listC.clear()
        self.listD.clear()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
