import io
import base64
from odoo import fields, models, api
from odoo.tools.misc import xlsxwriter
from datetime import datetime, timedelta
import pytz

class RepairReports(models.Model):
    _name = "repair.reports"
    _description = "Repair Reports"
    _rec_name = 'display_name'

    location_ids = fields.Many2many('res.company', domain=[('parent_id', '!=', False)], string='Location', required=True, default=lambda self: self._default_location_ids())
    start_date = fields.Date(string="Start Date", required=True, default=lambda self: fields.Date.today() - timedelta(days=7))
    end_date = fields.Date(string="End Date", required=True, default=fields.Date.today())
    shipping_line_ids = fields.Many2many(
        "res.partner",
        string="Shipping Line",
        domain="[('is_shipping_line', '=', True)]"
    )

    type_size_ids = fields.Many2many("container.type.data", string="Container Type/Size")
    display_name = fields.Char(
        string="Repair Reports",
        default= "Repair Reports"
    )

    @api.model
    def _default_location_ids(self):

        locations = self.env['res.company'].search([('parent_id', '!=', False)])

        return locations if len(locations) == 1 else self.env['res.company']

    def action_email_report(self):
        """Send mail with the attached repair report."""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        active_ids = self.env.context.get('active_ids', [])
        records = self.browse(active_ids)

        # Generate the sheets
        self._create_repair_report_sheet(workbook)
        self._create_mnr_current_repair_report_sheet(workbook)

        # Close the workbook and prepare for download
        workbook.close()
        output.seek(0)

        # Encode the output to base64 for attachment
        file_data = base64.b64encode(output.read())
        output.close()

        # Create a file record in Odoo (attachment)
        attachment = self.env['ir.attachment'].create({
            'name': 'Repair Report.xlsx',
            'type': 'binary',
            'datas': file_data,
            'store_fname': 'Repair Report.xlsx',
            'res_model': 'repair.reports',
            'res_id': self.id,
        })

        # Prepare the email template
        mail_values = {
            'subject': f"Repair Report between {self.start_date} - {self.end_date}",
            'body_html': f"""
                <p>Dear Sir/Madam,</p>
                <p>Please find attached the Repair report between {self.start_date} - {self.end_date}.</p>
                <p>Regards,</p>
                <p>CMS Team</p>
            """,
            'email_from': self.env.user.email,
            'attachment_ids': [(6, 0, [attachment.id])],
            'email_to': 'demo@mail.com',
        }

        # Send the email
        mail = self.env['mail.mail'].create(mail_values)
        mail.send()

        return {
            'type': 'ir.actions.act_window_close',
        }

    def _create_repair_report_sheet(self, workbook):
        """Create MNR excel report for repair pending estimates"""
        worksheet = workbook.add_worksheet('MNR Report')
        # Define border format for cells with a right border
        border_right_format = workbook.add_format({'right': 1})
        general_report_header_format = workbook.add_format(
            {'bg_color': '#f4cccc', 'font_color': 'black', 'bold': True, 'border': 1})
        westim_header_format = workbook.add_format(
            {'bg_color': '#D9B3FF', 'font_color': 'black', 'bold': True, 'border': 1})
        destim_header_format = workbook.add_format(
            {'bg_color': '#D9EAF7', 'font_color': 'black', 'bold': True, 'border': 1})
        destim_status_header_format = workbook.add_format(
            {'bg_color': '#4D4D4D', 'font_color': 'black', 'bold': True, 'border': 1})

        worksheet.merge_range(0, 0, 0, 15, 'General Reports', general_report_header_format)

        general_reports_sub_headers = ['Sr. No.', 'Depot Name', 'Depot Code', 'Location', 'Shipping Line',
                                       'Repair Vendor Name', 'Repair Vendor / GVA Code', 'Estimate Month',
                                       'Estimate Year', 'Estimate Date', 'Container No.', 'Container Type/Size',
                                       'Production Month/Year', 'Repair Status', 'Move Code', 'Move In Date/Time']
        worksheet.write_row(1, 0, general_reports_sub_headers)

        worksheet.merge_range(0, 16, 0, 38, 'Estimate Details / WESTIM Details', westim_header_format)

        westim_details_sub_headers = ['WESTIM Reference No.', 'Item No.', 'Damage Remarks', 'Repair Code',
                                      'Damage Location', 'Damage Type', 'Component', 'Repair Type',
                                      'Material Type', 'Key Value', 'Limit', 'Qty', 'Labor Rate',
                                      'Man Hrs(Tariff)', 'Material(Tariff)',
                                      'GST %', 'Man Hrs (Cost)', 'Material Cost (INR)',
                                      'Total Cost (INR)', 'GST Amount', 'Total Cost (INR) WITH GST',
                                      'Grand Total Cost (INR)']
        worksheet.write_row(1, 16, westim_details_sub_headers)

        worksheet.merge_range(0, 39, 0, 46, 'Approval Details / DESTIM Details', destim_header_format)

        destim_details_sub_headers = ['Shipping Line Status', 'Qty', 'Man Hrs (Cost)', 'Material Cost (INR)',
                                      'Total Cost (INR)', 'GST Amount', 'Total Cost (INR) WITH GST',
                                      'Remarks', 'Status']
        worksheet.write_row(1, 39, destim_details_sub_headers)

        worksheet.merge_range(0, 48, 0, 49, 'DESTIM Response',destim_status_header_format)

        destim_response_sub_headers = ['Repair Completion Date']
        worksheet.write_row(1, 48, destim_response_sub_headers)

        sr_no = 1
        row_index = 2
        item_no = 1

        domain = [
            ('location_id', 'in', self.location_ids.ids),  # Use 'in' for multiple locations
            ('estimate_date_and_time', '>=', self.start_date),
            ('estimate_date_and_time', '<=', self.end_date)
        ]

        if self.type_size_ids:
            domain.append(('pending_id.type_size_id', '=', self.type_size_ids.ids))

        if self.shipping_line_ids:
            domain.append(('pending_id.shipping_line_id', 'in', self.shipping_line_ids.ids))

        estimate_records = self.env['repair.pending.estimates'].search(domain)

        for estimate_record in estimate_records:
            for shipping_mapping in estimate_record.location_id.shipping_line_mapping_ids:
                if shipping_mapping.shipping_line_id.id == estimate_record.shipping_line_id.id:
                    depot_name = shipping_mapping.depot_name
                    depot_code = shipping_mapping.depot_code
                    if shipping_mapping.repair_vendor_is_same_company == 'yes':
                        repair_vendor =shipping_mapping.company_id.parent_id.name
                    else:
                        repair_vendor =shipping_mapping.repair_vendor_name
                    repair_vendor_gva_code = shipping_mapping.repair_vendor_code
                    labour_rate = shipping_mapping.labour_rate

                    estimate_datetime = estimate_record.estimate_date_and_time

                    if estimate_datetime:
                        # Extract details
                        estimate_month = estimate_datetime.month
                        estimate_year = estimate_datetime.year
                        estimate_date = estimate_datetime.date().strftime('%Y-%m-%d')
                        container_number = estimate_record.container_no
                        container_type_size = estimate_record.pending_id.type_size_id.name
                        estimate_month1 = estimate_record.month
                        estimate_year1 = estimate_record.year
                        production_month_year = f"{estimate_month1}-{estimate_year1}"
                        location_name = estimate_record.location_id.name
                        shipping_line_name = estimate_record.shipping_line_id.name
                        repair_status_dict = dict(
                                        estimate_record._fields['repair_status']._description_selection(
                                            estimate_record.env))
                        repair_status = repair_status_dict.get(estimate_record.repair_status, '')
                        move_code = "MIR"
                        move_in_date_time = estimate_record.pending_id.move_in_date_time
                        if isinstance(move_in_date_time, datetime):
                        # If it's already a datetime object, just format it
                                    move_in_date_time = move_in_date_time.strftime('%Y-%m-%d')
                        elif move_in_date_time:  # If it's a timestamp (float), convert it
                            move_in_date_time = datetime.fromtimestamp(move_in_date_time).strftime(
                                '%Y-%m-%d %H:%M:%S')
                        else:
                            move_in_date_time = ' '
                        westim_reference_number= estimate_record.pending_id.estimate_number
                        gst_amount = estimate_record.total_tax
                        grand_total_cost = estimate_record.grand_total

                        previous_estimate_record = None
                        merge_start_row = None
                        estimate_lines = estimate_record.estimate_line_ids
                        for estimate_line in estimate_lines:
                            damage_remarks = estimate_line.description
                            if shipping_mapping.refer_container == "no":
                                damage_location = estimate_line.damage_location_id.damage_location
                                damage_type = estimate_line.damage_type.damage_type_code
                                component = estimate_line.component.code
                                repair_type = estimate_line.repair_type.repair_type_code
                                material_type = estimate_line.material_type.code
                                repair_code = estimate_line.repair_code_id.repair_code
                                limit = estimate_line.limit_id.limit
                                man_hrs = estimate_line.tarrif_id.labour_hour
                            else:
                                damage_location = estimate_line.damage_location_text
                                damage_type = estimate_line.damage_type_text
                                component = estimate_line.component_text
                                repair_type = estimate_line.repair_type_text
                                material_type = estimate_line.material_type_text
                                repair_code = estimate_line.repair_code
                                man_hrs = estimate_line.labour_hour_text
                                limit = estimate_line.limit_text

                            key_value = estimate_line.key_value.name
                            quantity = estimate_line.qty
                            material_hrs = "0"
                            gst_percent = "18%"
                            man_hrs_cost = estimate_line.labour_cost
                            material_hrs_cost = estimate_line.material_cost
                            total_cost = estimate_line.total
                            total_cost_with_gst = gst_amount + total_cost

                            worksheet.write(row_index, 0, sr_no, border_right_format)
                            worksheet.write(row_index, 1, depot_name, border_right_format)
                            worksheet.write(row_index, 2, depot_code, border_right_format)
                            worksheet.write(row_index, 3, location_name, border_right_format)
                            worksheet.write(row_index, 4, shipping_line_name, border_right_format)
                            worksheet.write(row_index, 5, repair_vendor, border_right_format)
                            worksheet.write(row_index, 6, repair_vendor_gva_code, border_right_format)

                            # Write the estimate data in the current row
                            worksheet.write(row_index, 7, estimate_month, border_right_format)
                            worksheet.write(row_index, 8, estimate_year, border_right_format)
                            worksheet.write(row_index, 9, estimate_date, border_right_format)
                            worksheet.write(row_index, 10, container_number, border_right_format)
                            worksheet.write(row_index, 11, container_type_size, border_right_format)
                            worksheet.write(row_index, 12, production_month_year, border_right_format)
                            worksheet.write(row_index, 13, repair_status, border_right_format)
                            worksheet.write(row_index, 14, move_code, border_right_format)
                            worksheet.write(row_index, 15, move_in_date_time, border_right_format)
                            worksheet.write(row_index, 16, westim_reference_number, border_right_format)
                            worksheet.write(row_index, 17, item_no, border_right_format)
                            worksheet.write(row_index, 18, damage_remarks, border_right_format)
                            worksheet.write(row_index, 19, repair_code, border_right_format)
                            worksheet.write(row_index, 20, damage_location, border_right_format)
                            worksheet.write(row_index, 21, damage_type, border_right_format)
                            worksheet.write(row_index, 22, component, border_right_format)
                            worksheet.write(row_index, 23, repair_type, border_right_format)
                            worksheet.write(row_index, 24, material_type, border_right_format)
                            worksheet.write(row_index, 25, key_value, border_right_format)
                            worksheet.write(row_index, 26, limit, border_right_format)
                            worksheet.write(row_index, 27, quantity, border_right_format)
                            worksheet.write(row_index, 28, labour_rate, border_right_format)
                            worksheet.write(row_index, 29, man_hrs, border_right_format)
                            # worksheet.write(row_index, 30, cleaning_cost, border_right_format)
                            worksheet.write(row_index, 30, material_hrs, border_right_format)
                            worksheet.write(row_index, 31, gst_percent, border_right_format)
                            worksheet.write(row_index, 32, man_hrs_cost, border_right_format)
                            worksheet.write(row_index, 33, material_hrs_cost, border_right_format)
                            worksheet.write(row_index, 34, total_cost, border_right_format)
                            worksheet.write(row_index, 35, gst_amount, border_right_format)
                            worksheet.write(row_index, 36, total_cost_with_gst, border_right_format)
                            worksheet.write(row_index, 37, grand_total_cost, border_right_format)
                            if previous_estimate_record == estimate_record:
                                worksheet.merge_range(merge_start_row, 37, row_index, 37, grand_total_cost, border_right_format)
                            else:
                                previous_estimate_record = estimate_record
                                merge_start_row = row_index
                            # Increment the row index for the next record
                            sr_no +=1
                            item_no +=1
                            row_index += 1

    def _create_mnr_current_repair_report_sheet(self, workbook):
        """Create MNR current report for repair pending estimates."""
        worksheet = workbook.add_worksheet('MNR Current Report')

        headers = ['Sr. No.',	'Month',	'Year',	'Repair', 'Vendor Name',	'Container No.',
                   'Size/Type',	'Move Code',	'Arrival Date',	'Depot Code',	'Depot Name',	'Location',
                   'Mfg Year',	'Mfg Month',	'Item No.',	'Damage Remark',	'Repair Code',	'Qty',
                   'Man Hrs(Tariff)',	'Material(Tariff)',	'Cleaning Cost(Tariff)',	'GST %',
                   'Man Hrs (Cost)',	'Material Cost (INR)'	'Cleaning Cost (INR)'	'Total Cost (INR)',
                   'GST Amount',	'Total Cost (INR) WITH GST',	'Grand Total Cost (INR)',	'50']

        # Create header format with bottom border
        header_format = workbook.add_format({
            'font_color': 'black',
            'bold': True,
            'border': 1,  # Add border to header cells
        })

        # Write headers only
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, header_format)





