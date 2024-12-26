# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from .contrainer_type_edi import ContainerTypeEdi
from .res_users import ResUsers
import base64
import io
import xlsxwriter


class LoloCharge(models.Model):
    _name = 'lolo.charge'
    _rec_name = 'display_name'
    _description = 'Lolo Charges'

    shipping_line_logo = fields.Binary(string="Shipping Line", related="shipping_line.logo")
    location = fields.Many2one('res.company', string="Location", domain="[('parent_id', '!=', False)]")
    shipping_line = fields.Many2one('res.partner', string="Shipping Line", domain="[('is_shipping_line', '=', True)]")
    lolo_charge_lines = fields.One2many("lolo.charge.lines", "lolo_charge_id", string="Lolo Charges")
    charges_for = fields.Char("Charges for", compute="_append_charges")
    active = fields.Boolean("Status", default=True)
    rec_status = fields.Selection([
        ('active', 'Active'),
        ('disable', 'Disable'),
    ], default="active", compute="_check_active_records", string="Status")
    display_create_info = fields.Char(compute="_get_create_record_info")
    display_modified_info = fields.Char(compute="_get_modify_record_info")

    def _compute_display_name(self):
        """Computes and sets the display name based on location, shipping line, and currency."""
        for record in self:
            location_name = record.location.name if record.location else ' '
            shipping_line_name = record.shipping_line.name if record.shipping_line else ' '
            record.display_name = f'{location_name} - {shipping_line_name}'

    def _append_charges(self):
        for rec in self:
            charges = []
            for val in rec.lolo_charge_lines:
                charges.append(val.container_size)
            charges_val = ','.join(charges)
            rec.charges_for = charges_val

    def _check_active_records(self):
        ContainerTypeEdi.check_active_records(self)

    def _get_create_record_info(self):
        """
        Assign create record log string to the appropriate field.
        :return: none
        """
        for rec in self:
            if rec.env.user.tz and rec.create_uid:
                tz_create_date = ResUsers.convert_datetime_to_user_timezone(rec.env.user, rec.create_date)
                create_uid_name = rec.create_uid.name
                if tz_create_date:
                    rec.display_create_info = ResUsers.get_user_log_data(rec, tz_create_date, create_uid_name)
            else:
                rec.display_create_info = ''

    def _get_modify_record_info(self):
        """
            Assign update record log string to the appropriate field.
            :return: none
        """
        for rec in self:
            if self.env.user.tz and rec.write_uid:
                tz_write_date = ResUsers.convert_datetime_to_user_timezone(rec.env.user, rec.write_date)
                write_uid_name = rec.write_uid.name
                if tz_write_date:
                    rec.display_modified_info = ResUsers.get_user_log_data(rec, tz_write_date, write_uid_name)
            else:
                rec.display_modified_info = ''

    # @api.model
    # def download_xlsx_file(self, **kwargs):
    #     return {
    #         'type': 'ir.actions.act_url',
    #         'url': '/empezar_base/static/src/reports/LoLoUploadSample.xlsx',
    #         'target': 'new',
    #     }

    @api.model
    def download_xlsx_file(self, **kwargs):
        # Fetch all unique active locations from the lolo.charge model

        # Fetch all active locations from res.company
        active_locations = self.env['res.company'].search([('active', '=', True), ('parent_id', '!=', False)])

        # Create an in-memory output file for the new workbook
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        worksheet.set_column(0, 0, 25)
        worksheet.set_column(2, 2, 15)
        worksheet.set_column(4, 4, 15)
        worksheet.set_column(6, 6, 15)
        worksheet.set_column(8, 8, 15)
        # Define your formats
        header_format = workbook.add_format(
            {'font_color': 'black', 'bold': True, 'border': 1})
        lift_off_header_format = workbook.add_format(
            {'bg_color': '#9AC0CD', 'font_color': 'black', 'bold': True, 'border': 1})  # Blue
        lift_on_header_format = workbook.add_format(
            {'bg_color': '#b6d7a8', 'font_color': 'black', 'bold': True, 'border': 1})  # Green
        lift_subheader_format = workbook.add_format(
            {'bg_color': 'white', 'font_color': 'black', 'bold': True, 'border': 1})
        border_right_format = workbook.add_format({'right': 1})
        bold_format = workbook.add_format({'bold': True})
        bottom_border_format = workbook.add_format({'bottom': 1})

        # Write the main header for Location
        worksheet.merge_range(0, 0, 1, 0, 'Location Name (Code)', header_format)

        # Write Lift OFF and Lift ON main headings in the first row
        worksheet.merge_range(0, 1, 0, 4, 'Lift OFF', lift_off_header_format)
        worksheet.merge_range(0, 5, 0, 8, 'Lift ON', lift_on_header_format)

        # Write the sub-headers for Lift OFF and Lift ON
        lift_off_sub_headers = ['20 FT', '20 FT Reefer', '40 FT', '40 FT Reefer']
        lift_on_sub_headers = ['20 FT', '20 FT Reefer', '40 FT', '40 FT Reefer']
        worksheet.write_row(1, 1, lift_off_sub_headers, lift_subheader_format)
        worksheet.write_row(1, 5, lift_on_sub_headers, lift_subheader_format)

        max_row = len(active_locations)
        for row in range(2, max_row + 2):
            worksheet.write(row, 1, '', border_right_format)
            worksheet.write(row, 2, '', border_right_format)
            worksheet.write(row, 3, '', border_right_format)
            worksheet.write(row, 4, '', border_right_format)
            worksheet.write(row, 5, '', border_right_format)
            worksheet.write(row, 6, '', border_right_format)
            worksheet.write(row, 7, '', border_right_format)
            worksheet.write(row, 8, '', border_right_format)

        # Iterate through the active locations and add them to the worksheet
        # Iterate through the active locations and add them to the worksheet
        for index, location in enumerate(active_locations, start=2):
            # Combine location name and code
            location_display = f"{location.name} ({location.location_code})"
            worksheet.write(index, 0, location_display, border_right_format)
            
        # Finalize the workbook
        workbook.close()
        # Prepare the response for the file download
        output.seek(0)
        file_data = base64.b64encode(output.read())
        output.close()

        # Create an attachment for the file
        attachment = self.env['ir.attachment'].create({
            'name': 'LoLoUploadSample.xlsx',
            'type': 'binary',
            'datas': file_data,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        # Return the action to download the file from the attachment
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%d/%s' % (attachment.id, attachment.name),
            'target': 'new',
            'download': True,
        }
