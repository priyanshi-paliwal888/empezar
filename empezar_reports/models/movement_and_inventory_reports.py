# -*- coding: utf-8 -*-
import io
import base64
import pytz
from datetime import date, datetime, timedelta
from collections import defaultdict
from odoo import fields, models,api
from odoo.tools.misc import xlsxwriter
from odoo.addons.empezar_base.models.res_users import ResUsers
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import ValidationError

class MovementAndInventoryReports(models.Model):
    _name = "movement.and.inventory.reports"
    _description = "Movement And Inventory Reports"
    _rec_name = 'name'

    name= fields.Char(string="Movement And Inventory Reports", default="Movement And Inventory Reports")
    location_ids = fields.Many2many('res.company', domain=[('parent_id', '!=', False)], string='Location', required=True, default=lambda self: self._default_location_ids())

    shipping_line_ids = fields.Many2many(
        "res.partner",
        string="Shipping Line",
        domain="[('is_shipping_line', '=', True)]"
    )
    type_size_ids = fields.Many2many("container.type.data", string="Container Type/Size")
    is_move_in = fields.Boolean(string="Detailed-Move In",default=True)
    is_move_out = fields.Boolean(string="Detailed-Move Out", default=True)
    is_inventory = fields.Boolean(string="Detailed-Inventory", default=True)
    is_summary_movement = fields.Boolean(string="Summary-Movement with Throughput")
    is_summary_TAT = fields.Boolean(string="Summary-TAT")
    is_summary_ageing = fields.Boolean(string="Summary-Ageing")
    is_summary_stock_report = fields.Boolean(string="Summary-Stock Report")
    is_summary_inventory_container_status = fields.Boolean(string="Summary-Container Status")
    move_in_date_range = fields.Date(string="Move In Date", default=fields.Date.today())
    move_in_date_range_start = fields.Date(string="Move In Date Start", default=fields.Date.today())
    move_out_date_range = fields.Date(string="Move Out Date", default=fields.Date.today())
    move_out_date_range_start = fields.Date(string="Move Out Date Start", default=fields.Date.today())
    as_on_date = fields.Date(string="As On Date", default=fields.Date.today())
    movement_date_range = fields.Date(string="Movement Date", default=fields.Date.today())
    movement_date_range_start = fields.Date(string="Movement Date Start",default=fields.Date.today() )


    @api.model
    def _default_location_ids(self):

        locations = self.env['res.company'].search([('parent_id', '!=', False)])

        return locations if len(locations) == 1 else self.env['res.company']

    def action_clear(self):
        self.is_move_in = False
        self.is_move_out = False
        self.is_inventory = False
        self.is_summary_movement = False
        self.is_summary_TAT = False
        self.is_summary_ageing = False
        self.is_summary_stock_report = False
        self.is_summary_inventory_container_status = False

    def action_send_combined_reports(self):
        """Create and send the combined reports as attachments in an email."""

        report_sections = []
        attachment_ids = []
        output = io.BytesIO()
        if self.is_move_in:
            workbook = xlsxwriter.Workbook(output)
            self._create_move_in_report_sheet(workbook)

            workbook.close()
            move_in_output = output.getvalue()

            move_in_attachment = self.env['ir.attachment'].create({
            'name': 'Detailed - Move In.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(move_in_output),
            'store_fname': 'Detailed - Move In.xlsx',
            'res_model': 'movement.and.inventory.reports',
            'res_id': False,
            })
            attachment_ids.append(move_in_attachment.id)
            report_sections.append('Detailed - Move In')

        output = io.BytesIO()
        if self.is_move_out:
            move_out_workbook = xlsxwriter.Workbook(output)
            self._create_move_out_report_sheet(move_out_workbook)

            move_out_workbook.close()
            move_out_output = output.getvalue()

            move_out_attachment = self.env['ir.attachment'].create({
                'name': 'Detailed - Move Out.xlsx',
                'type': 'binary',
                'datas': base64.b64encode(move_out_output),
                'store_fname': 'Detailed - Move Out.xlsx',
                'res_model': 'movement.and.inventory.reports',
                'res_id': False,
            })
            attachment_ids.append(move_out_attachment.id)
            report_sections.append('Detailed - Move Out')

        output = io.BytesIO()
        if self.is_inventory:
            inventory_workbook = xlsxwriter.Workbook(output)
            self._create_inventory_report_sheet(inventory_workbook)

            inventory_workbook.close()
            output.seek(0)

            file_data = base64.b64encode(output.read())
            output.close()

            inventory_attachment = self.env['ir.attachment'].create({
                'name': 'Detailed - Inventory.xlsx',
                'type': 'binary',
                'datas': file_data,
                'store_fname': 'Detailed - Inventory.xlsx',
                'res_model': 'movement.and.inventory.reports',
                'res_id': False,
            })
            attachment_ids.append(inventory_attachment.id)
            report_sections.append('Detailed - Inventory')

        output = io.BytesIO()
        if self.is_summary_movement:
            summary_movement_workbook = xlsxwriter.Workbook(output)
            self._create_movement_with_throughput_report_sheet(summary_movement_workbook)
            self._create_movement_with_throughput_report_by_shipping_line(summary_movement_workbook)

            summary_movement_workbook.close()
            output.seek(0)

            file_data = base64.b64encode(output.read())
            output.close()

            summary_movement_attachment = self.env['ir.attachment'].create({
                'name': 'Summary - Movement with Throughput.xlsx',
                'type': 'binary',
                'datas': file_data,
                'store_fname': 'Summary - Movement with Throughput.xlsx',
                'res_model': 'movement.and.inventory.reports',
                'res_id': False,
            })
            attachment_ids.append(summary_movement_attachment.id)
            report_sections.append('Summary - Movement with Throughput')

        output = io.BytesIO()
        if self.is_summary_TAT:
            summary_TAT_workbook = xlsxwriter.Workbook(output)

            self._create_container_TAT(summary_TAT_workbook)
            self._create_container_TAT_by_shipping_line(summary_TAT_workbook)

            summary_TAT_workbook.close()
            output.seek(0)

            file_data = base64.b64encode(output.read())
            output.close()

            summary_TAT_attachment = self.env['ir.attachment'].create({
                'name': 'Summary - TAT.xlsx',
                'type': 'binary',
                'datas': file_data,
                'store_fname': 'Summary - TAT.xlsx',
                'res_model': 'movement.and.inventory.reports',
                'res_id': False,
            })
            attachment_ids.append(summary_TAT_attachment.id)
            report_sections.append('Summary - TAT')

        output = io.BytesIO()
        if self.is_summary_ageing:
            summary_ageing_workbook = xlsxwriter.Workbook(output)

            self._create_summary_ageing_report_sheet(summary_ageing_workbook)
            self._create_summary_ageing_report_by_shipping_line(summary_ageing_workbook)

            summary_ageing_workbook.close()
            output.seek(0)

            file_data = base64.b64encode(output.read())
            output.close()

            summary_ageing_attachment = self.env['ir.attachment'].create({
                'name': 'Summary - Ageing.xlsx',
                'type': 'binary',
                'datas': file_data,
                'store_fname': 'Summary - Ageing.xlsx',
                'res_model': 'movement.and.inventory.reports',
                'res_id': False,
            })
            attachment_ids.append(summary_ageing_attachment.id)
            report_sections.append('Summary - Ageing')

        output = io.BytesIO()
        if self.is_summary_stock_report:
            summary_stock_report_workbook = xlsxwriter.Workbook(output)

            self._create_summary_stock_report(summary_stock_report_workbook)
            self._create_summary_stock_report_by_shipping_line(summary_stock_report_workbook)

            summary_stock_report_workbook.close()
            output.seek(0)

            file_data = base64.b64encode(output.read())
            output.close()

            summary_stock_attachment = self.env['ir.attachment'].create({
                'name': 'Summary Stock Report.xlsx',
                'type': 'binary',
                'datas': file_data,
                'store_fname': 'Summary Stock Report .xlsx',
                'res_model': 'movement.and.inventory.reports',
                'res_id': False,
            })
            attachment_ids.append(summary_stock_attachment.id)
            report_sections.append('Summary Stock Report')

        output = io.BytesIO()
        if self.is_summary_inventory_container_status:
            summary_inventory_container_status_workbook = xlsxwriter.Workbook(output)
            self. _create_summary_container_status(summary_inventory_container_status_workbook)
            self._create_summary_container_status_by_shipping_line(summary_inventory_container_status_workbook)

            summary_inventory_container_status_workbook.close()
            output.seek(0)

            file_data = base64.b64encode(output.read())
            output.close()

            summary_inventory_container_status_attachment = self.env['ir.attachment'].create({
                'name': 'Summary - Container Status.xlsx',
                'type': 'binary',
                'datas': file_data,
                'store_fname': 'Summary - Container Status .xlsx',
                'res_model': 'movement.and.inventory.reports',
                'res_id': False,
            })
            attachment_ids.append(summary_inventory_container_status_attachment.id)
            report_sections.append('Summary - Container Status')
        # dynamic_body = "".join(report_sections)
        dynamic_body = "".join(f"<p>{section}</p>" for section in report_sections)
        mail_values = {
            'subject': 'Movement and Inventory Report - Combined',
            'body_html': """
                <p>Dear Sir/Madam,</p>
                <p>Please find attached the following reports.</p>
                {}
                <p>Regards,</p>
                <p>CMS Teams</p>
            """.format(dynamic_body),
            'email_from': self.env.user.email,
            'attachment_ids': [(6, 0, attachment_ids)],
            'email_to': 'demo@mail.com',
        }
        if not any ([self.is_move_in, self.is_move_out, self.is_inventory, self.is_summary_movement, self.is_summary_TAT, self.is_summary_ageing, self.is_summary_stock_report, self.is_summary_inventory_container_status]):
            raise ValidationError("Please select atleast one report to send.")

        mail = self.env['mail.mail'].create(mail_values)
        mail.send()
        self.is_move_in= True
        self.is_move_out = True
        self.is_inventory = True
        self.is_summary_movement = False
        self.is_summary_TAT = False
        self.is_summary_ageing = False
        self.is_summary_stock_report = False
        self.is_summary_inventory_container_status = False
        self.shipping_line_ids = False
        self.type_size_ids = False
        self.move_in_date_range = fields.Date.today()
        self.move_in_date_range_start = fields.Date.today()
        self.move_out_date_range = fields.Date.today()
        self.move_out_date_range_start = fields.Date.today()
        self.as_on_date = fields.Date.today()
        self.movement_date_range = fields.Date.today()
        self.movement_date_range_start = fields.Date.today()
        return {
            'type': 'ir.actions.act_window_close',
        }

    def _create_move_in_report_sheet(self, workbook):
        """Create a worksheet for the Move In report."""

        worksheet = workbook.add_worksheet('Move in Report')

        headers = [
            'Sr. No.', 'Location', 'Shipping Line', 'Container No.',
            'Type/Size', 'Container Type / Size (ISO)', 'Gross Weight (KG)', 'Tare Weight (KG)',
            'Payload (KG)', 'Production Month/Year', 'Grade', 'Damage', 'Patch Count', 'Container Status',
            'Seal No 1', 'Seal No 2', 'Move In Date', 'Move In Time', 'Movement Type', 'Arrival From/From',
            'Importer', 'Laden Status', 'Mode', 'Transporter (Allotted)', 'Transporter (Fulfilled)',
            'Truck No.', 'Driver Name', 'Driver Mobile Number', 'Driver License Number', 'Rake No.', 'Wagon No.',
            'Stack', 'Booking Type', 'DO/Booking Validity Date/Time', 'Lift Off Inv. No', 'Lift Off Amount', 'GST No.',
            'Additional Invoice No.', 'Additional Invoice Amount', 'In EDI Sent', 'Damage EDI Sent', 'Gate Pass No.',
            'Created By', 'Created On Date/Time', 'Remarks'
        ]

        header_format = workbook.add_format({
            'font_color': 'black',
            'bold': True,
            'border': 1,
        })

        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, header_format)
        domain = [('location_id', 'in', self.location_ids.ids)]
        if self.shipping_line_ids:
            domain.append(('shipping_line_id', 'in', self.shipping_line_ids.ids))
        if self.type_size_ids:
            domain.append(('type_size_id', 'in', self.type_size_ids.ids))
        start_date = self.move_in_date_range_start
        end_date = self.move_in_date_range
        if start_date and end_date:
            domain.append(('move_in_date_time', '>=', start_date))
            domain.append(('move_in_date_time', '<=', end_date))
        local_tz = pytz.timezone('Asia/Kolkata')
        move_in_records = self.env['move.in'].search(domain)
        row_num = 1
        for record in move_in_records:
            if record.move_in_date_time:
            # Separate date and time
                local_dt = pytz.utc.localize(record.move_in_date_time).astimezone(local_tz)
                move_in_date = record.move_in_date_time.strftime('%Y-%m-%d')  # Format to 'YYYY-MM-DD'
                move_in_time = local_dt.strftime('%H:%M:%S')  # Format to 'HH:MM:SS'
            else:
                move_in_date = ''
                move_in_time = ''
            if record.do_validity_datetime:
                do_validity_datetime_local = pytz.utc.localize(record.do_validity_datetime).astimezone(local_tz)
            if record.movement_type == 'import_destuffing':
                if record.import_destuffing_from == 'factory':
                    arrival_from_from = 'From Factory'
                elif record.import_destuffing_from == 'CFS/ICD':
                    arrival_from_from = 'From CFS/ICD'
            elif record.movement_type == 'repo':
                if record.repo_from == 'port_terminal':
                    arrival_from_from = f'From {record.from_port.port_name}/{record.from_terminal.port_name}'
                elif record.repo_from == 'CFS/ICD':
                    arrival_from_from = 'From CFS/ICD'
                elif record.repo_from == 'empty_yard':
                    arrival_from_from = 'From Factory'
            else:
                arrival_from_from = ''
            invoice_records = self.env['move.in.out.invoice'].search([('move_in_id', '=', record.id)])
            gst_no = [invoice.billed_to_gst_no.gst_no for invoice in invoice_records if invoice.billed_to_gst_no ]
            gst_no = ', '.join(gst_no) if gst_no else ''
            lift_off_invoices = [invoice.invoice_number for invoice in invoice_records if invoice.invoice_type == 'lift_off']
            invoice_numbers = ', '.join(lift_off_invoices) if lift_off_invoices else ''
            lift_off_amounts = [str(invoice.total_amount) for invoice in invoice_records if invoice.invoice_type == 'lift_off']
            # invoice_amounts = ', '.join(str(lift_off_amounts)) if lift_off_amounts else ''
            other_invoices = [invoice.invoice_number for invoice in invoice_records if invoice.invoice_type != 'lift_off']
            other_invoice_numbers = ', '.join(other_invoices) if other_invoices else ''
            other_amounts = [str(invoice.total_amount) for invoice in invoice_records if invoice.invoice_type != 'lift_off']
            # other_invoice_amounts = ', '.join(str(other_amounts)) if other_amounts else ''
            tz_create_date = ResUsers.convert_datetime_to_user_timezone(record.env.user,
                                                            record.create_date)
            tz_create_date_str = tz_create_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            tz_create_date_naive = datetime.strptime(tz_create_date_str, DEFAULT_SERVER_DATETIME_FORMAT)
            movement_type_dict = dict(record._fields['movement_type'].selection)
            movement_type_label = movement_type_dict.get(record.movement_type, '')
            stack_dict = dict(record._fields['stack'].selection)  # Fetch selection options as a dictionary
            stack_label = stack_dict.get(record.stack, '')
            edi_log = self.env['edi.logs'].search([('move_in_ids', '=', record.id)],limit=1)
            edi_sent_on = edi_log.edi_sent_on.strftime('%Y-%m-%d %H:%M:%S') if edi_log else ''

            worksheet.write(row_num, 0, row_num)
            worksheet.write(row_num, 1, record.location_id.name if record.location_id else '')
            worksheet.write(row_num, 2, record.shipping_line_id.name if record.shipping_line_id else '')
            worksheet.write(row_num, 3, record.container)
            worksheet.write(row_num, 4, record.type_size_id.name if record.type_size_id else '')
            worksheet.write(row_num, 5, 0)
            worksheet.write(row_num, 6, record.gross_wt)
            worksheet.write(row_num, 7, record.tare_wt)
            worksheet.write(row_num, 8, int(record.gross_wt) - int(record.tare_wt))
            worksheet.write(row_num, 9, record.month)
            worksheet.write(row_num, 10, record.grade)
            worksheet.write(row_num, 11, record.damage_condition.name)
            worksheet.write(row_num, 12, record.patch_count if record.patch_count else '')
            worksheet.write(row_num, 13, record.container_status)
            worksheet.write(row_num, 14, record.seal_no_1 if record.seal_no_1 else '')
            worksheet.write(row_num, 15, record.seal_no_2 if record.seal_no_2 else '')
            worksheet.write(row_num, 16, move_in_date)
            worksheet.write(row_num, 17, move_in_time)
            worksheet.write(row_num, 18, movement_type_label)
            worksheet.write(row_num, 19, arrival_from_from)
            worksheet.write(row_num, 20, record.parties_importer.name if record.parties_importer else '')
            worksheet.write(row_num, 21, record.laden_status)
            worksheet.write(row_num, 22, record.mode)
            worksheet.write(row_num, 23, record.transporter_allotment_id.name if record.transporter_allotment_id else '')
            worksheet.write(row_num, 24, record.transporter_full_filled_id.name if record.transporter_full_filled_id else '')
            worksheet.write(row_num, 25, record.truck_no if record.truck_no else '')
            worksheet.write(row_num, 26, record.driver_name if record.driver_name else '')
            worksheet.write(row_num, 27, record.driver_mobile_no if record.driver_mobile_no else '')
            worksheet.write(row_num, 28, record.driver_licence_no if record.driver_licence_no else '')
            worksheet.write(row_num, 29, record.rake_no if record.rake_no else '')
            worksheet.write(row_num, 30, record.wagon_no if record.wagon_no else '')
            worksheet.write(row_num, 31, stack_label)
            worksheet.write(row_num, 32, record.do_no_id.delivery_no if record.do_no_id else '')
            worksheet.write(row_num, 33, do_validity_datetime_local.strftime('%Y-%m-%d %H:%M:%S') if record.do_validity_datetime else '')
            worksheet.write(row_num, 34, invoice_numbers)
            worksheet.write(row_num, 35, ",".join(lift_off_amounts))
            worksheet.write(row_num, 36, gst_no)
            worksheet.write(row_num,37,other_invoice_numbers)
            worksheet.write(row_num, 38,  ",".join(other_amounts))
            worksheet.write(row_num, 39, edi_sent_on)
            worksheet.write(row_num, 40, 0)
            worksheet.write(row_num, 41, record.gate_pass_no if record.gate_pass_no else '')
            worksheet.write(row_num, 42, record.create_uid.name)
            worksheet.write(row_num, 43, tz_create_date_naive.strftime('%Y-%m-%d %H:%M:%S'))
            worksheet.write(row_num, 44, record.remarks if record.remarks else '')
            # Continue for other columns as needed
            row_num += 1

    def _create_move_out_report_sheet(self, move_out_workbook):
        """Create a worksheet for the Move Out report."""

        worksheet = move_out_workbook.add_worksheet('Move Out Report')

        headers = [
            'Sr. No.', 'Location', 'Shipping Line', 'Is Shipping Line Interchanged?', 'Original Shipping Line','Container No.',
            'Type/Size', 'Container Type / Size (ISO)', 'Gross Weight (KG)', 'Tare Weight (KG)',
            'Payload (KG)', 'Production Month/Year', 'Move In Grade', 'Move In Damage', 'Move Out Grade', 'Container Status',
            'Seal No 1', 'Seal No 2', 'Temperature','Humidity','Vent','Vent Seal No.','Laden Status','Move In Date','Move In Time','Move Out Date', 'Move Out Time', 'TAT ','Movement Type',
            'To Location',	'Booking Type',	'DO/Booking No.', 'DO/Booking Validity Date/TIme',	'Vessel',	'Voyage',	'POD',	'Exporter',	'Mode',	'Transporter (Allotted)',	'Transporter (Fulfilled)',
            'Truck Number',	'Driver Name',	'Driver Mobile Number',	'Driver License Number',	'Rake No.',	'Wagon No.',	'Stack',	'Lift On Inv. No',	'Lift On Amount	','GST No.',
            'Additional Invoice No. & Amt',	'Invoice Amount',	'Out EDI Sent',	'Repair EDI Sent',	'Gate Pass No.', 'Created By', 'Created On Date/Time',	'Remarks']

        header_format = move_out_workbook.add_format({
            'font_color': 'black',
            'bold': True,
            'border': 1,
        })

        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, header_format)

        domain = [('location_id', 'in', self.location_ids.ids)]
        if self.shipping_line_ids:
            domain.append(('shipping_line_id', 'in', self.shipping_line_ids.ids))
        if self.type_size_ids:
            domain.append(('type_size_id', 'in', self.type_size_ids.ids))
        start_date = self.move_out_date_range_start
        end_date = self.move_out_date_range
        if start_date and end_date:
            domain.append(('move_out_date_time', '>=', start_date))
            domain.append(('move_out_date_time', '<=', end_date))
        move_out_records = self.env['move.out'].search(domain)
        local_tz = pytz.timezone('Asia/Kolkata')
        row_num = 1
        for record in move_out_records:
            if record.move_in_date_time:
                local_dt = pytz.utc.localize(record.move_in_date_time).astimezone(local_tz)
                move_in_date = record.move_in_date_time.strftime('%Y-%m-%d')  # Format to 'YYYY-MM-DD'
                move_in_time = local_dt.strftime('%H:%M:%S')  # Format to 'HH:MM:SS'
            else:
                move_in_date = ''
                move_in_time = ''

            if record.move_in_id.move_in_date_time:
                local_dt = pytz.utc.localize(record.move_in_id.move_in_date_time).astimezone(local_tz)
                move_in_date = record.move_in_id.move_in_date_time.strftime('%Y-%m-%d')  # Format to 'YYYY-MM-DD'
                move_in_time = local_dt.strftime('%H:%M:%S')  # Format to 'HH:MM:SS'
            else:
                move_in_date = ''
                move_in_time = ''
            if record.move_out_date_time:
                local_dt = pytz.utc.localize(record.move_out_date_time).astimezone(local_tz)
                move_out_time = local_dt.strftime('%H:%M:%S')
            if record.validity_datetime:
                validity_datetime_local = pytz.utc.localize(record.validity_datetime).astimezone(local_tz)
            if record.movement_type == 'export_stuffing':
                if record.export_stuffing_to == 'factory':
                    location_to = 'From Factory'
                elif record.export_stuffing_to == 'CFS/ICD':
                    location_to = 'From CFS/ICD'
            elif record.movement_type == 'repo':
                if record.repo_to == 'port_terminal':
                    location_to = 'From Port/Terminal'
                elif record.repo_to == 'CFS/ICD':
                    location_to = 'From CFS/ICD'
                elif record.repo_to == 'empty_yard':
                    location_to = 'From Factory'
            else:
                location_to = ''

            if record.booking_no_id:
                vessel = record.booking_no_id.vessel
                voyage = record.booking_no_id.voyage
                pod = record.booking_no_id.port_discharge.port_name
            if record.delivery_order_id:
                vessel = record.delivery_order_id.vessel
                voyage = record.delivery_order_id.voyage
                pod = record.delivery_order_id.port_discharge.port_name

            invoice_records = self.env['move.in.out.invoice'].search([('move_out_id', '=', record.id)])
            gst_no = [invoice.billed_to_gst_no.gst_no for invoice in invoice_records if invoice.billed_to_gst_no ]
            gst_no = ', '.join(gst_no) if gst_no else ''
            lift_on_invoices = [invoice.invoice_number for invoice in invoice_records if invoice.invoice_type == 'lift_on']
            invoice_numbers = ', '.join(lift_on_invoices) if lift_on_invoices else ''
            lift_on_amounts = [str(invoice.total_amount) for invoice in invoice_records if invoice.invoice_type == 'lift_on']
            # invoice_amounts = ', '.join(str(lift_off_amounts)) if lift_off_amounts else ''
            other_invoices = [invoice.invoice_number for invoice in invoice_records if invoice.invoice_type != 'lift_on']
            other_invoice_numbers = ', '.join(other_invoices) if other_invoices else ''
            other_amounts = [str(invoice.total_amount) for invoice in invoice_records if invoice.invoice_type != 'lift_on']
            # other_invoice_amounts = ', '.join(str(other_amounts)) if other_amounts else ''
            tz_create_date = ResUsers.convert_datetime_to_user_timezone(record.env.user,
                                                            record.create_date)
            tz_create_date_str = tz_create_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            tz_create_date_naive = datetime.strptime(tz_create_date_str, DEFAULT_SERVER_DATETIME_FORMAT)
            movement_type_dict = dict(record._fields['movement_type'].selection)
            movement_type_label = movement_type_dict.get(record.movement_type, '')
            tat = max((record.move_out_date_time - record.move_in_id.move_in_date_time).days,0) if record.move_out_date_time and record.move_in_id.move_in_date_time  else 0
            edi_log = self.env['edi.logs'].search([('move_out_ids', '=', record.id)], limit=1)
            edi_sent_on = edi_log.edi_sent_on.strftime('%Y-%m-%d %H:%M:%S') if edi_log else ''

            worksheet.write(row_num, 0, row_num)
            worksheet.write(row_num, 1, record.location_id.name if record.location_id else '')
            worksheet.write(row_num, 2, record.shipping_line_id.name if record.shipping_line_id else '')
            worksheet.write(row_num, 3, record.is_shipping_line_interchange)
            worksheet.write(row_num, 4, record.move_in_id.shipping_line_id.name if record.shipping_line_id else '')
            worksheet.write(row_num, 5, record.inventory_id.name if record.inventory_id else '')
            worksheet.write(row_num, 6, record.type_size_id.name if record.type_size_id else '')
            worksheet.write(row_num, 7, 0)
            worksheet.write(row_num, 8, record.gross_wt)
            worksheet.write(row_num, 9, record.tare_wt)
            worksheet.write(row_num, 10, record.gross_wt - record.tare_wt)
            worksheet.write(row_num, 11, record.production_month_year)
            worksheet.write(row_num, 12, record.move_in_id.grade if record.move_in_id.grade else '')
            worksheet.write(row_num, 13, record.move_in_id.damage_condition.name if record.move_in_id.damage_condition else '')
            worksheet.write(row_num, 14, record.grade if record.grade else '')
            worksheet.write(row_num, 15, record.container_status if record.container_status else '')
            worksheet.write(row_num, 16, record.seal_no_1.id if record.seal_no_1 else '')
            worksheet.write(row_num, 17, record.seal_no_2.id if record.seal_no_2 else '')
            worksheet.write(row_num, 18, record.temperature if record.temperature else '')
            worksheet.write(row_num, 19, record.humidity if record.humidity else '')
            worksheet.write(row_num, 20, record.vent if record.vent else '')
            worksheet.write(row_num, 21, record.vent_seal_no if record.vent_seal_no else '')
            worksheet.write(row_num, 22, record.laden_status if record.laden_status else '')
            worksheet.write(row_num, 23, move_in_date)
            worksheet.write(row_num, 24, move_in_time)
            worksheet.write(row_num, 25, record.move_out_date_time.strftime('%Y-%m-%d') if record.move_out_date_time else '')
            worksheet.write(row_num, 26, move_out_time if record.move_out_date_time else '')
            worksheet.write(row_num, 27, tat)
            worksheet.write(row_num, 28, movement_type_label)
            worksheet.write(row_num, 29, location_to)
            worksheet.write(row_num, 30, record.booking_no_id.booking_no if record.booking_no_id else '')
            worksheet.write(row_num, 31, record.delivery_order_id.delivery_no if record.delivery_order_id else '')
            worksheet.write(row_num, 32, validity_datetime_local.strftime('%Y-%m-%d %H:%M:%S') if record.validity_datetime else '')
            worksheet.write(row_num, 33, vessel if vessel else '')
            worksheet.write(row_num, 34, voyage if voyage else '')
            worksheet.write(row_num, 35, pod if pod else '')
            worksheet.write(row_num, 36, record.exporter_delivery_order_id.name if record.exporter_delivery_order_id else '')
            worksheet.write(row_num, 37, record.mode)
            worksheet.write(row_num, 38, record.transporter_allocated_id.name if record.transporter_allocated_id else '')
            worksheet.write(row_num, 39, record.transporter_fulfilled_id.name if record.transporter_fulfilled_id else '')
            worksheet.write(row_num, 40, record.truck_number if record.truck_number else '')
            worksheet.write(row_num, 41, record.driver_name if record.driver_name else '')
            worksheet.write(row_num, 42, record.driver_mobile_number if record.driver_mobile_number else '')
            worksheet.write(row_num, 43, record.driver_licence_no if record.driver_licence_no else '')
            worksheet.write(row_num, 44, record.rake_number if record.rake_number else '')
            worksheet.write(row_num, 45, record.wagon_number if record.wagon_number else '')
            worksheet.write(row_num, 46, record.stack)
            worksheet.write(row_num, 47, invoice_numbers)
            worksheet.write(row_num, 48, ",".join(lift_on_amounts))
            worksheet.write(row_num, 49, gst_no)
            worksheet.write(row_num, 50, other_invoice_numbers)
            worksheet.write(row_num, 51, ",".join(other_amounts))
            worksheet.write(row_num, 52, edi_sent_on)
            worksheet.write(row_num, 53, 0)
            worksheet.write(row_num, 54, record.gate_pass_no if record.gate_pass_no else '')
            worksheet.write(row_num, 55, record.create_uid.name)
            worksheet.write(row_num, 56, tz_create_date_naive.strftime('%Y-%m-%d %H:%M:%S'))
            worksheet.write(row_num, 57, record.remark if record.remark else '')
            row_num += 1

    def _create_inventory_report_sheet(self, workbook):
        """Create a worksheet for the Inventory report."""

        worksheet = workbook.add_worksheet('Inventory Report')

        headers =['Sr. No.', 'Location', 'Shipping Line', 'Container No.', 'Type/Size', 'Type/Size (ISO)',
                'Production Month/Year',	'Gross Weight (Kg)', 'Tare Weight (Kg)', 'Payload',	'Move In Grade',
                'Move In Damage', 'Container Status','Move In Date', 'Move In Time', 'Estimate Date', 'Estimate Amount',
                'Approval Date', 'Approved Amount' ,'Repair Date', 'Dwell Days', 'Hold Reason']

        header_format = workbook.add_format({
            'font_color': 'black',
            'bold': True,
            'border': 1,
        })

        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, header_format)

        local_tz = pytz.timezone('Asia/Kolkata')
        inventory_records = self.env['container.inventory'].search([('location_id', 'in', self.location_ids.ids)])
        row_num = 1
        for record in inventory_records:
            move_in_record = self.env['move.in'].search([
                ('location_id', '=', record.location_id.id),
                ('container', '=', record.name)
            ], limit=1)
            dwell_days = (date.today() - move_in_record.move_in_date_time.date()).days if move_in_record.move_in_date_time else 0
            if record.move_in_id.move_in_date_time:
                local_dt = pytz.utc.localize(record.move_in_id.move_in_date_time).astimezone(local_tz)
                move_in_time = local_dt.strftime('%H:%M:%S')
            worksheet.write(row_num, 0, row_num)
            worksheet.write(row_num, 1, record.location_id.name if record.location_id else '')
            worksheet.write(row_num, 2, record.move_in_id.shipping_line_id.name if record.move_in_id.shipping_line_id else '')
            worksheet.write(row_num, 3, record.name)
            worksheet.write(row_num, 4, move_in_record.type_size_id.name if move_in_record.type_size_id else '')
            worksheet.write(row_num, 5, 0)
            worksheet.write(row_num, 6, f"{move_in_record.month}-{move_in_record.year}" if move_in_record.month and move_in_record.year else '') 
            worksheet.write(row_num, 7, move_in_record.gross_wt if move_in_record.gross_wt else '')
            worksheet.write(row_num, 8, move_in_record.tare_wt if move_in_record.tare_wt else '')
            worksheet.write(row_num, 9, int(move_in_record.gross_wt) - int(move_in_record.tare_wt))
            worksheet.write(row_num, 10, move_in_record.grade if move_in_record.grade else '')
            worksheet.write(row_num, 11, move_in_record.damage_condition.name if move_in_record.damage_condition else '')
            worksheet.write(row_num, 12, record.status)
            worksheet.write(row_num, 13, move_in_record.move_in_date_time.strftime('%Y-%m-%d') if move_in_record.move_in_date_time else '')
            worksheet.write(row_num, 14, move_in_time if move_in_record.move_in_date_time else '')
            worksheet.write(row_num, 15, record.estimate_date.strftime('%Y-%m-%d') if record.estimate_date else '')
            worksheet.write(row_num, 16, record.estimate_amount)
            worksheet.write(row_num, 17, record.approval_date.strftime('%Y-%m-%d') if record.approval_date else '')
            worksheet.write(row_num, 18, record.approved_amount)
            worksheet.write(row_num, 19, record.repair_date.strftime('%Y-%m-%d') if record.repair_date else '')
            worksheet.write(row_num, 20, dwell_days)
            worksheet.write(row_num, 21, 0)
            row_num += 1

    def _create_movement_with_throughput_report_sheet(self, workbook):
        """Create a worksheet for the Movement with Throughput report."""

        worksheet = workbook.add_worksheet('Group By - Location')

        header_format = workbook.add_format({
            'font_color': 'black',
            'bold': True,
            'border': 1,
        })

        worksheet.write(1, 0, 'Location', header_format)
        worksheet.write(1, 1, 'Shipping Line', header_format)

        worksheet.merge_range(0, 2, 0, 6, 'Move  In', header_format)
        worksheet.merge_range(0, 7, 0, 11, 'Move Out', header_format)

        move_in_sub_headers = ['Dry 20 FT','Dry 40 FT',	'RF 20 FT',	'RF 40 FT',	'TEUs']
        move_out_sub_headers = ['Dry 20 FT',	'Dry 40 FT',	'RF 20 FT',	'RF 40 FT',	'TEUs']
        worksheet.write_row(1, 2, move_in_sub_headers, header_format)
        worksheet.write_row(1, 7, move_out_sub_headers, header_format)

        worksheet.write(1, 12, ' Throughput (TEUs)', header_format)

        row_num = 2
        prev_location = None
        start_row = row_num
        for location in self.env['res.company'].search([('id', 'in', self.location_ids.ids)]):
            if self.shipping_line_ids:
                shipping_line_ids = self.shipping_line_ids.ids
            else:
                shipping_line_ids = location.shipping_line_mapping_ids.mapped(
                            "shipping_line_id"
                        ).ids
            for shipping in shipping_line_ids:

                sizes_20ft =['20FT Reefer', '20FT']
                sizes_40ft =['40FT Reefer', '40FT']
                dry_20_ft = self._get_container_count(location.id, self.env['res.partner'].browse(shipping), sizes_20ft, 'no', 1)
                dry_40_ft = self._get_container_count(location.id, self.env['res.partner'].browse(shipping),sizes_40ft, 'no', 2)
                rf_20_ft = self._get_container_count(location.id, self.env['res.partner'].browse(shipping), sizes_20ft, 'yes', 1)
                rf_40_ft = self._get_container_count(location.id, self.env['res.partner'].browse(shipping),sizes_40ft, 'yes', 2)
                dry_20_ft_move_out = self._get_container_count_move_out(location.id, self.env['res.partner'].browse(shipping), sizes_20ft, 'no', 1)
                dry_40_ft_move_out = self._get_container_count_move_out(location.id, self.env['res.partner'].browse(shipping),sizes_40ft, 'no', 2)
                rf_20_ft_move_out = self._get_container_count_move_out(location.id, self.env['res.partner'].browse(shipping), sizes_20ft, 'yes', 1)
                rf_40_ft_move_out = self._get_container_count_move_out(location.id, self.env['res.partner'].browse(shipping),sizes_40ft, 'yes', 2)
                teus = dry_20_ft + dry_40_ft*2 + rf_20_ft + rf_40_ft*2
                teus_move_out = dry_20_ft_move_out + dry_40_ft_move_out*2 + rf_20_ft_move_out + rf_40_ft_move_out*2
                throughput = teus + teus_move_out
                worksheet.write(row_num, 0, location.name)
                worksheet.write(row_num, 1, self.env['res.partner'].browse(shipping).name)
                worksheet.write(row_num, 2, dry_20_ft)
                worksheet.write(row_num, 3, dry_40_ft)
                worksheet.write(row_num, 4, rf_20_ft)
                worksheet.write(row_num, 5, rf_40_ft)
                worksheet.write(row_num, 6, teus)
                worksheet.write(row_num, 7, dry_20_ft_move_out)
                worksheet.write(row_num, 8, dry_40_ft_move_out)
                worksheet.write(row_num, 9, rf_20_ft_move_out)
                worksheet.write(row_num, 10, rf_40_ft_move_out)
                worksheet.write(row_num, 11, teus_move_out)
                worksheet.write(row_num, 12, throughput)
                if prev_location == location.name:
                    worksheet.merge_range(start_row, 0, row_num, 0, location.name)  # Merge cells in the location column
                else:
                    start_row = row_num  # Update the start row for the next potential merge

                prev_location = location.name
                row_num += 1

    def _get_container_count(self, location_id, shipping, size, is_refer, te_us):
        """Get the count of containers based on the given parameters."""
        move_in_records = self.env['move.in'].search([
                    ('location_id', '=', location_id),
                    ('shipping_line_id', '=', shipping.id),
                    ('move_in_date_time', '>=', self.movement_date_range_start),
                    ('move_in_date_time', '<=', self.movement_date_range)
                ])
        count = 0
        for record in move_in_records:
            if record.type_size_id and record.type_size_id.is_refer and record.type_size_id.te_us:
                if record.type_size_id.size in size and record.type_size_id.is_refer == is_refer and (
                (te_us == 1 and record.type_size_id.te_us == 1) or 
                (te_us == 2 and record.type_size_id.te_us >= 2) ):
                    count += 1
        return count

    def _get_container_count_move_out(self,location_id, shipping, size, is_refer, te_us):
        """Get the count of containers based on the given parameters."""
        move_out_records = self.env['move.out'].search([
                    ('location_id', '=', location_id),
                    ('shipping_line_id', '=', shipping.id),
                    ('move_out_date_time', '>=', self.movement_date_range_start),
                    ('move_out_date_time', '<=', self.movement_date_range)
                ])
        count = 0
        for record in move_out_records:
            if record.type_size_id and record.type_size_id.is_refer and record.type_size_id.te_us:
                if record.type_size_id.size in size and record.type_size_id.is_refer == is_refer and (
                (te_us == 1 and record.type_size_id.te_us == 1) or 
                (te_us == 2 and record.type_size_id.te_us >= 2) ):
                    count += 1
        return count

    def _create_movement_with_throughput_report_by_shipping_line(self, workbook):
        worksheet = workbook.add_worksheet('Group By - Shipping Line')

        header_format = workbook.add_format({
            'font_color': 'black',
            'bold': True,
            'border': 1,
        })

        worksheet.write(1, 0, 'Shipping Line', header_format)
        worksheet.write(1, 1, 'Location')

        worksheet.merge_range(0, 2, 0, 6, 'Move  In', header_format)
        worksheet.merge_range(0, 7, 0, 11, 'Move Out', header_format)

        # Write the sub-headers for Move Out and Move IN
        move_in_sub_headers = ['Dry 20 FT','Dry 40 FT',	'RF 20 FT',	'RF 40 FT',	'TEUs']
        move_out_sub_headers = ['Dry 20 FT',	'Dry 40 FT',	'RF 20 FT',	'RF 40 FT',	'TEUs']
        worksheet.write_row(1, 2, move_in_sub_headers, header_format)
        worksheet.write_row(1, 7, move_out_sub_headers, header_format)

        worksheet.write(1, 12, ' Throughput (TEUs)', header_format)
        row_num = 2
        previous_shipping_line = None
        start_row = 2
        if self.shipping_line_ids:
            shipping_lines = self.shipping_line_ids
            
        else:
            shipping_lines = self.env['res.partner'].search([('is_shipping_line', '=', True)])
        
        for shipping_line in shipping_lines:
            if self.shipping_line_ids:
                locations = self.env['res.company'].search([
                    ('id', 'in', self.location_ids.ids)
                ])
            else:
                locations = self.env['res.company'].search([
                    ('shipping_line_mapping_ids.shipping_line_id', '=', shipping_line.id),('id', 'in', self.location_ids.ids)
                ])
            for location in locations:
                sizes_20ft =['20FT Reefer', '20FT']
                sizes_40ft =['40FT Reefer', '40FT']
                dry_20_ft = self._get_container_count(location.id, shipping_line, sizes_20ft, 'no', 1)
                dry_40_ft = self._get_container_count(location.id, shipping_line, sizes_40ft, 'no', 2)
                rf_20_ft = self._get_container_count(location.id, shipping_line, sizes_20ft, 'yes', 1)
                rf_40_ft = self._get_container_count(location.id, shipping_line, sizes_40ft, 'yes', 2)

                dry_20_ft_move_out = self._get_container_count_move_out(location.id, shipping_line, sizes_20ft, 'no', 1)
                dry_40_ft_move_out = self._get_container_count_move_out(location.id, shipping_line, sizes_40ft, 'no', 2)
                rf_20_ft_move_out = self._get_container_count_move_out(location.id, shipping_line, sizes_20ft, 'yes', 1)
                rf_40_ft_move_out = self._get_container_count_move_out(location.id, shipping_line, sizes_40ft, 'yes', 2)

                teus = dry_20_ft + dry_40_ft*2 + rf_20_ft + rf_40_ft*2
                teus_move_out = dry_20_ft_move_out + dry_40_ft_move_out*2 + rf_20_ft_move_out + rf_40_ft_move_out*2
                throughput = teus + teus_move_out

                if shipping_line.name != previous_shipping_line:
                    if previous_shipping_line is not None:
                        worksheet.merge_range(start_row, 0, row_num - 1, 0, previous_shipping_line)

                    previous_shipping_line = shipping_line.name
                    start_row = row_num 
                worksheet.write(row_num, 0, shipping_line.name)
                worksheet.write(row_num, 1, location.name)
                worksheet.write(row_num, 2, dry_20_ft)
                worksheet.write(row_num, 3, dry_40_ft)
                worksheet.write(row_num, 4, rf_20_ft)
                worksheet.write(row_num, 5, rf_40_ft)
                worksheet.write(row_num, 6, teus)
                worksheet.write(row_num, 7, dry_20_ft_move_out)
                worksheet.write(row_num, 8, dry_40_ft_move_out)
                worksheet.write(row_num, 9, rf_20_ft_move_out)
                worksheet.write(row_num, 10, rf_40_ft_move_out)
                worksheet.write(row_num, 11, teus_move_out)
                worksheet.write(row_num, 12, throughput)
                row_num += 1
        if previous_shipping_line is not None:
            worksheet.merge_range(start_row, 0, row_num - 1, 0, previous_shipping_line)

    def _create_summary_ageing_report_sheet(self, workbook):
        """Create a worksheet for the Summary Ageing report."""

        worksheet = workbook.add_worksheet('Group By - Location')

        header_format = workbook.add_format({
            'font_color': 'black',
            'bold': True,
            'border': 1,
        })

        worksheet.write(1, 0, 'Location', header_format)
        worksheet.write(1, 1, 'Shipping Line', header_format)

        worksheet.merge_range(0, 2, 0, 9, 'Container Count', header_format)

        container_days_sub_headers = ['0-3 Days', '4-7 Days', '8-15 Days', '16-30 Days', '31-60 Days',
                                      '61-90 Days',	'91-180 Days',	'>180 Days']

        worksheet.write_row(1, 2, container_days_sub_headers, header_format) 

        worksheet.write(1, 10, ' Total', header_format)
        domain = [('location_id', 'in', self.location_ids.ids),('move_in_date', '<=', self.as_on_date)]
        if self.shipping_line_ids:
            master_record = self.env['container.master'].search([('shipping_line_id', 'in', self.shipping_line_ids.ids)]).mapped('name')
            domain.append(('name', 'in', master_record))
        inventory_record = self.env['container.inventory'].search(domain)
        grouped_counts = defaultdict(lambda: [0] * len(container_days_sub_headers))

        # Iterate over each inventory record
        for record in inventory_record:
            shipping_line = record.container_master_id.shipping_line_id
            if record.move_in_date:
                dwell_days = (self.as_on_date - record.move_in_date).days
                if dwell_days <= 3:
                    grouped_counts[(record.location_id.name, shipping_line.name)][0] += 1  # 0-3 days
                elif dwell_days <= 7:
                    grouped_counts[(record.location_id.name, shipping_line.name)][1] += 1  # 4-7 days
                elif dwell_days <= 15:
                    grouped_counts[(record.location_id.name, shipping_line.name)][2] += 1  # 8-15 days
                elif dwell_days <= 30:
                    grouped_counts[(record.location_id.name, shipping_line.name)][3] += 1  # 16-30 days
                elif dwell_days <= 60:
                    grouped_counts[(record.location_id.name, shipping_line.name)][4] += 1  # 31-60 days
                elif dwell_days <= 90:
                    grouped_counts[(record.location_id.name, shipping_line.name)][5] += 1  # 61-90 days
                elif dwell_days <= 180:
                    grouped_counts[(record.location_id.name, shipping_line.name)][6] += 1  # 91-180 days
                else:
                    grouped_counts[(record.location_id.name, shipping_line.name)][7] += 1  # >180 days

        sorted_grouped_counts = sorted(grouped_counts.items(), key=lambda x: (x[0][0], x[0][1]))

        row_num = 2  # Starting row for writing data
        prev_location = None  # To track the previous location for merging
        start_row = 2  # To track the starting row for merging each location

        for (location, shipping_line), container_count in sorted_grouped_counts:
            # Merge cells for the location if it's different from the previous one
            if prev_location is not None and location != prev_location:
                # Merge location column for previous location
                if start_row < row_num - 1:
                    worksheet.merge_range(start_row, 0, row_num - 1, 0, prev_location)
                start_row = row_num  # Update start_row for the new location

            # Write data
            worksheet.write(row_num, 0, location)  # Location
            worksheet.write(row_num, 1, shipping_line)  # Shipping Line
            worksheet.write_row(row_num, 2, container_count)  # Container Counts
            worksheet.write(row_num, 10, sum(container_count))  # Total containers

            prev_location = location  # Update prev_location
            row_num += 1  # Move to the next row

        # Merge cells for the last location
        if start_row < row_num - 1:
            worksheet.merge_range(start_row, 0, row_num - 1, 0, prev_location)

    def _create_summary_ageing_report_by_shipping_line(self, workbook):
        """Create a worksheet for the Summary Ageing report by Shipping Line."""

        worksheet = workbook.add_worksheet('Group By - Shipping Line')

        header_format = workbook.add_format({
            'font_color': 'black',
            'bold': True,
            'border': 1,
        })

        worksheet.write(1, 0, 'Shipping Line', header_format)   
        worksheet.write(1, 1, 'Location', header_format)

        worksheet.merge_range(0, 2, 0, 9, 'Container Count', header_format)

        container_days_sub_headers = ['0-3 Days', '4-7 Days', '8-15 Days', '16-30 Days', '31-60 Days',
                                    '61-90 Days', '91-180 Days', '>180 Days']
        worksheet.write_row(1, 2, container_days_sub_headers, header_format)
        worksheet.write(1, 10, 'Total', header_format)
        domain = [('location_id', 'in', self.location_ids.ids),('move_in_date', '<=', self.as_on_date)]

        if self.shipping_line_ids:
            master_record = self.env['container.master'].search([('shipping_line_id', 'in', self.shipping_line_ids.ids)]).mapped('name')
            domain.append(('name', 'in', master_record))
        inventory_record = self.env['container.inventory'].search(domain)

        # Dictionary to store container counts grouped by shipping line and location
        grouped_counts = defaultdict(lambda: defaultdict(lambda: [0] * len(container_days_sub_headers)))

        row_num = 2
        prev_shipping_line = None
        start_row = 2
        # Iterate over each move_in_record
        for record in inventory_record:
            shipping_line = record.container_master_id.shipping_line_id
            location = record.location_id

            # Calculate dwell days
            if record.move_in_date:
                dwell_days = (self.as_on_date - record.move_in_date).days

            # Determine the category based on dwell_days
                if dwell_days <= 3:
                    grouped_counts[shipping_line.name][location.name][0] += 1  # 0-3 days
                elif dwell_days <= 7:
                    grouped_counts[shipping_line.name][location.name][1] += 1  # 4-7 days
                elif dwell_days <= 15:
                    grouped_counts[shipping_line.name][location.name][2] += 1  # 8-15 days
                elif dwell_days <= 30:
                    grouped_counts[shipping_line.name][location.name][3] += 1  # 16-30 days
                elif dwell_days <= 60:
                    grouped_counts[shipping_line.name][location.name][4] += 1  # 31-60 days
                elif dwell_days <= 90:
                    grouped_counts[shipping_line.name][location.name][5] += 1  # 61-90 days
                elif dwell_days <= 180:
                    grouped_counts[shipping_line.name][location.name][6] += 1  # 91-180 days
                else:
                    grouped_counts[shipping_line.name][location.name][7] += 1  # >180 days

        row_num = 2
        prev_shipping_line = None
        start_row = 2
        for shipping_line, locations in grouped_counts.items():
             
            if prev_shipping_line is not None and shipping_line != prev_shipping_line:
                if start_row < row_num - 1:
                    worksheet.merge_range(start_row, 0, row_num - 1, 0, prev_shipping_line)
                start_row = row_num

            first_location = True
            for location, container_count in locations.items():
                if first_location:
                    worksheet.write(row_num, 0, shipping_line)
                    first_location = False
                worksheet.write(row_num, 1, location)
                worksheet.write_row(row_num, 2, container_count)
                worksheet.write(row_num, 10, sum(container_count))
                row_num += 1   

            prev_shipping_line = shipping_line 
        if start_row < row_num - 1:
            worksheet.merge_range(start_row, 0, row_num - 1, 0, prev_shipping_line)

    def _create_summary_stock_report(self, workbook):
        """Create a worksheet for the Summary Stock report."""

        worksheet = workbook.add_worksheet('Group By - Location')

        headers =['Location', 	'Shipping Line',	'Dry 20 FT',	'Dry 40 FT',
                'RF 20 FT',	'RF 20 FT',	'Total', 'TEUs',	'Yard Occupancy']

        header_format = workbook.add_format({
            'font_color': 'black',
            'bold': True,
            'border': 1,
        })
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, header_format)

        row_num = 1
        start_row = 1
        for location in self.env['res.company'].search([('id', 'in', self.location_ids.ids)]):
            if self.shipping_line_ids:
                shipping_line_ids = self.shipping_line_ids.ids
            else:
                shipping_line_ids = location.shipping_line_mapping_ids.mapped(
                            "shipping_line_id"
                        ).ids
            start_row = row_num
            for shipping in shipping_line_ids:
                sizes_20ft =['20FT Reefer', '20FT']
                sizes_40ft =['40FT Reefer', '40FT']
                dry_20_ft = self._get_container_count_stock(location.id, self.env['res.partner'].browse(shipping), sizes_20ft, 'no', 1)
                dry_40_ft = self._get_container_count_stock(location.id, self.env['res.partner'].browse(shipping), sizes_40ft, 'no', 2)
                rf_20_ft = self._get_container_count_stock(location.id, self.env['res.partner'].browse(shipping), sizes_20ft, 'yes', 1)
                rf_40_ft = self._get_container_count_stock(location.id, self.env['res.partner'].browse(shipping), sizes_40ft, 'yes', 2)

                total= dry_20_ft + dry_40_ft + rf_20_ft + rf_40_ft
                teus = dry_20_ft + dry_40_ft*2 + rf_20_ft + rf_40_ft*2
                yard_occupancy = (total/int(location.capacity))*100
                #worksheet.write(row_num, 0, location.name)
                worksheet.write(row_num, 1, self.env['res.partner'].browse(shipping).name)
                worksheet.write(row_num, 2, dry_20_ft)
                worksheet.write(row_num, 3, dry_40_ft)
                worksheet.write(row_num, 4, rf_20_ft)
                worksheet.write(row_num, 5, rf_40_ft)
                worksheet.write(row_num, 6, total)
                worksheet.write(row_num, 7, teus)
                worksheet.write(row_num, 8, yard_occupancy)
                row_num += 1
                if row_num > start_row + 1:
                    worksheet.merge_range(start_row, 0, row_num - 1, 0, location.name)
                else:
                    worksheet.write(start_row, 0, location.name)

    def _get_container_count_stock(self, location_id, shipping, size, is_refer, te_us):
        """Get the count of containers based on the given parameters."""
        # container_inventory = self.env['container.inventory'].search([('location_id', '=', location_id)])
        domain = [('location_id', '=', location_id),('move_in_date', '<=', self.as_on_date)]
        if self.shipping_line_ids:
            master_record = self.env['container.master'].search([('shipping_line_id', 'in', self.shipping_line_ids.ids)]).mapped('name')
            domain.append(('name', 'in', master_record))
        inventory_record = self.env['container.inventory'].search(domain)
        count = 0
        for record in inventory_record:
            if record.container_master_id.shipping_line_id.id == shipping.id:
                if record.container_master_id.type_size.size in size and record.container_master_id.type_size.is_refer == is_refer and (
                (te_us == 1 and record.container_master_id.type_size.te_us == 1) or 
                (te_us == 2 and record.container_master_id.type_size.te_us >= 2) ):
                    count += 1
        return count

    def _create_summary_stock_report_by_shipping_line(self,workbook):
        """Create a worksheet for the Summary Stock report by Shipping Line."""

        worksheet = workbook.add_worksheet('Group By - Shipping Line')

        headers =['Shipping Line', 	'Location',	'Dry 20 FT',	'Dry 40 FT',
                'RF 20 FT',	'RF 20 FT',	'Total', 'TEUs',	'Yard Occupancy']

        header_format = workbook.add_format({
            'font_color': 'black',
            'bold': True,
            'border': 1,
        })

        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, header_format)
        row_num = 1
        if self.shipping_line_ids:
            shipping_lines = self.shipping_line_ids
            
        else:
            shipping_lines = self.env['res.partner'].search([('is_shipping_line', '=', True)])
        for shipping_line in shipping_lines:
            if self.shipping_line_ids:
                locations = self.env['res.company'].search([
                    ('id', 'in', self.location_ids.ids)
                ])
            else:
                locations = self.env['res.company'].search([
                    ('shipping_line_mapping_ids.shipping_line_id', '=', shipping_line.id),('id', 'in', self.location_ids.ids)
                ])
            first_row = row_num
            for location in locations:
                sizes_20ft =['20FT Reefer', '20FT']
                sizes_40ft =['40FT Reefer', '40FT']
                dry_20_ft = self._get_container_count_stock(location.id, shipping_line, sizes_20ft, 'no', 1)
                dry_40_ft = self._get_container_count_stock(location.id, shipping_line, sizes_40ft, 'no', 2)
                rf_20_ft = self._get_container_count_stock(location.id, shipping_line, sizes_20ft, 'yes', 1)
                rf_40_ft = self._get_container_count_stock(location.id, shipping_line, sizes_40ft, 'yes', 2)
                total= dry_20_ft + dry_40_ft + rf_20_ft + rf_40_ft
                teus = dry_20_ft + dry_40_ft*2 + rf_20_ft + rf_40_ft*2
                yard_occupancy = (total/int(location.capacity))*100
                #worksheet.write(row_num, 0, shipping_line.name)  # Shipping Line
                worksheet.write(row_num, 1, location.name)
                worksheet.write(row_num, 2, dry_20_ft)
                worksheet.write(row_num, 3, dry_40_ft)
                worksheet.write(row_num, 4, rf_20_ft)
                worksheet.write(row_num, 5, rf_40_ft)
                worksheet.write(row_num, 6, total)
                worksheet.write(row_num, 7, teus)
                worksheet.write(row_num, 8, yard_occupancy)
                row_num += 1

                last_row = row_num - 1
                if first_row != last_row:
                    worksheet.merge_range(first_row, 0, last_row, 0, shipping_line.name)
                else:
                    worksheet.write(first_row, 0, shipping_line.name)

    def _create_summary_container_status(self, workbook):
        """Create a worksheet for the Summary Container Status report."""

        worksheet = workbook.add_worksheet('Group By - Location')
        header_format = workbook.add_format({
            'font_color': 'black',
            'bold': True,
            'border': 1,
        })
        worksheet.write(0, 0, 'Location', header_format)
        worksheet.write(0, 1, 'Shipping Line', header_format)
        worksheet.write(0, 2, 'Status', header_format)

        company_size_type_code =self.env['container.type.data'].search([]).mapped('company_size_type_code')
        dynamic_headers = []
        for size in company_size_type_code:
            dynamic_headers.append(size)
        worksheet.write_row(0, 3, dynamic_headers + ['Total'], header_format)

        static_statuses = ['AE', 'AA', 'AR', 'AV', 'DAV']
        row=1
        prev_location = None
        location_start_row = 1
        prev_shipping_line = None
        shipping_line_start_row = 1
        for location in self.env['res.company'].search([('id', 'in', self.location_ids.ids)]):
            if self.shipping_line_ids:
                shipping_line_ids = self.shipping_line_ids.ids
            else:
                shipping_line_ids = location.shipping_line_mapping_ids.mapped(
                            "shipping_line_id"
                        ).ids
            for shipping in shipping_line_ids:
                for status in static_statuses:
                    if prev_location is None or prev_location != location.name:
                        if prev_location is not None:
                            worksheet.merge_range(location_start_row, 0, row - 1, 0, prev_location)
                        prev_location = location.name
                        location_start_row = row
                    # worksheet.write(row, 0, location.name)  # Location name
                    # worksheet.write(row, 1,  self.env['res.partner'].browse(shipping).name)  # Shipping line name

                    if prev_shipping_line is None or prev_shipping_line != self.env['res.partner'].browse(shipping).name:
                        if prev_shipping_line is not None:
                            worksheet.merge_range(shipping_line_start_row, 1, row - 1, 1, prev_shipping_line)
                        prev_shipping_line = self.env['res.partner'].browse(shipping).name
                        shipping_line_start_row = row
                    worksheet.write(row, 2, status)

                    total_count = 0
                    for col, size in enumerate(dynamic_headers, start=3):
                        count = self._get_container_count_status(location, shipping, status, size)
                        worksheet.write(row, col, count)
                        total_count += count
                        worksheet.write(row, len(dynamic_headers) + 3, total_count)
                    row += 1
                if prev_shipping_line is not None:
                    worksheet.merge_range(shipping_line_start_row, 1, row - 1, 1, prev_shipping_line)
            if prev_location is not None:
                worksheet.merge_range(location_start_row, 0, row - 1, 0, prev_location)

    def _get_container_count_status(self, location, shipping, status, size):
        """Get the count of containers based on the given parameters."""
        domain = [('location_id', '=', location.name),('move_in_date', '<=', self.as_on_date)]
        if self.shipping_line_ids:
            master_record = self.env['container.master'].search([('shipping_line_id', 'in', self.shipping_line_ids.ids)]).mapped('name')
            domain.append(('name', 'in', master_record))
        inventory_record = self.env['container.inventory'].search(domain)
        count = 0
        for record in inventory_record:
            if record.container_master_id.shipping_line_id.id == shipping:
                if record.status == status.lower() and record.container_master_id.type_size.company_size_type_code == size:
                    count += 1

        return count

    def _create_summary_container_status_by_shipping_line(self, workbook):
        """Create a worksheet for the Summary Container Status report by Shipping Line."""

        worksheet = workbook.add_worksheet('Group By - Shipping Line')
        header_format = workbook.add_format({
            'font_color': 'black',
            'bold': True,
            'border': 1,
        })
        worksheet.write(0, 0, 'Shipping Line', header_format)
        worksheet.write(0, 1, 'Location', header_format)
        worksheet.write(0, 2, 'Status', header_format)

        company_size_type_code =self.env['container.type.data'].search([]).mapped('company_size_type_code')
        dynamic_headers = []
        for size in company_size_type_code:
            dynamic_headers.append(size)
        worksheet.write_row(0, 3, dynamic_headers, header_format)

        static_statuses = ['AE', 'AA', 'AR', 'AV', 'DAV']
        row=1
        last_shipping_line = None
        last_location = None
        shipping_line_merge_start_row = None
        location_merge_start_row = None
        if self.shipping_line_ids:
            shipping_lines = self.shipping_line_ids
        else:
            shipping_lines = self.env['res.partner'].search([('is_shipping_line', '=', True)])
        for shipping_line in shipping_lines:
            if self.shipping_line_ids:
                locations = self.env['res.company'].search([
                    ('id', 'in', self.location_ids.ids)
                ])
            else:
                locations = self.env['res.company'].search([
                    ('shipping_line_mapping_ids.shipping_line_id', '=', shipping_line.id),('id', 'in', self.location_ids.ids)
                ])
            for location in locations:
                for status in static_statuses:

                    if shipping_line != last_shipping_line:
                        if last_shipping_line is not None:
                            worksheet.merge_range(shipping_line_merge_start_row, 0, row - 1, 0, last_shipping_line.name)
                        last_shipping_line = shipping_line
                        shipping_line_merge_start_row = row
                    if location != last_location:
                        if last_location is not None:
                            worksheet.merge_range(location_merge_start_row, 1, row - 1, 1, last_location.name)
                        last_location = location
                        location_merge_start_row = row
                    worksheet.write(row, 0, shipping_line.name)
                    worksheet.write(row, 1, location.name)
                    worksheet.write(row, 2, status)
                    total_count = 0
                    for col, size in enumerate(dynamic_headers, start=3):
                        count = self._get_container_count_status(location, shipping_line.id, status, size)
                        worksheet.write(row, col, count)
                        total_count += count
                        worksheet.write(row, len(dynamic_headers) + 3, total_count)
                    row += 1
        if last_shipping_line is not None:
            worksheet.merge_range(shipping_line_merge_start_row, 0, row - 1, 0, last_shipping_line.name)
        if last_location is not None:
            worksheet.merge_range(location_merge_start_row, 1, row - 1, 1, last_location.name)

    def _create_container_TAT(self, workbook):
        """Create a worksheet for the Container TAT report."""

        worksheet = workbook.add_worksheet('Group By - Location')

        headers = ['Location', 'Shipping Line', 'Container Count', 'Average TAT', 
                'Same Day', '1 to 3 Days', '4 to 7 Days', '08 to 15 Days', '16 to 30 Days',
                '31 to 60 Days', '61 to 90 Days', '91 to 180 Days', 'Greater than 180 Days']

        header_format = workbook.add_format({
            'font_color': 'black',
            'bold': True,
            'border': 1,
        })

        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, header_format)

        row = 1
        last_location_name = None
        location_start_row = None
        domain = [('location_id', 'in', self.location_ids.ids), ('active', '=', False),('move_out_date','<=', self.as_on_date)]
        # Get all the containers that match the relevant locations and shipping lines
        if self.shipping_line_ids:
            master_record = self.env['container.master'].search([('shipping_line_id', 'in', self.shipping_line_ids.ids)]).mapped('name')
            domain.append(('name', 'in', master_record))
        inventory_record = self.env['container.inventory'].search(domain)

        # Iterate over inventory records and calculate TAT categories
        grouped_counts = defaultdict(lambda: [0] * len(headers[3:]))  # To group data by (location, shipping_line)
        total_tat_days_by_shipping_line_and_location = {}
        for container in inventory_record:
            location = container.location_id.name
            shipping_line = container.container_master_id.shipping_line_id.name

            # Calculate TAT for each container
            if container.move_in_date and container.move_out_date:
                tat_days = (container.move_out_date - container.move_in_date).days

                # Initialize counters for each category
                tat_categories = {
                    'same_day': 0,
                    '1_to_3_days': 0,
                    '4_to_7_days': 0,
                    '8_to_15_days': 0,
                    '16_to_30_days': 0,
                    '31_to_60_days': 0,
                    '61_to_90_days': 0,
                    '91_to_180_days': 0,
                    'greater_than_180_days': 0
                }

                # Categorize the TAT days
                if tat_days == 0:
                    tat_categories['same_day'] += 1
                elif 1 <= tat_days <= 3:
                    tat_categories['1_to_3_days'] += 1
                elif 4 <= tat_days <= 7:
                    tat_categories['4_to_7_days'] += 1
                elif 8 <= tat_days <= 15:
                    tat_categories['8_to_15_days'] += 1
                elif 16 <= tat_days <= 30:
                    tat_categories['16_to_30_days'] += 1
                elif 31 <= tat_days <= 60:
                    tat_categories['31_to_60_days'] += 1
                elif 61 <= tat_days <= 90:
                    tat_categories['61_to_90_days'] += 1
                elif 91 <= tat_days <= 180:
                    tat_categories['91_to_180_days'] += 1
                else:
                    tat_categories['greater_than_180_days'] += 1

                # Update grouped counts
                tat_counts = grouped_counts[(location, shipping_line)]
                tat_counts[0] += 1  # Container count
                for idx, category in enumerate(tat_categories.values(), 1):  # Start from index 1
                    tat_counts[idx] += category
                if (location, shipping_line) not in total_tat_days_by_shipping_line_and_location:
                    total_tat_days_by_shipping_line_and_location[(location, shipping_line)] = 0

                total_tat_days_by_shipping_line_and_location[(location, shipping_line)] += tat_days
        # Write data to the worksheet
        for (location, shipping_line), counts in sorted(grouped_counts.items()):
            container_count = counts[0]
            # total_tat = sum(counts[1:])
            total_tat = total_tat_days_by_shipping_line_and_location[(location, shipping_line)]
            average_tat = total_tat / container_count if container_count > 0 else 0

            if location != last_location_name:
                if last_location_name is not None:
                    worksheet.merge_range(location_start_row, 0, row - 1, 0, last_location_name)

                last_location_name = location
                location_start_row = row

            worksheet.write(row, 0, location)  # Location
            worksheet.write(row, 1, shipping_line)  # Shipping Line
            worksheet.write(row, 2, container_count)  # Container Count
            worksheet.write(row, 3, round(average_tat, 2))  # Average TAT
            for i in range(9):  # Write TAT categories from columns 4 to 12
                worksheet.write(row, i + 4, counts[i + 1])  # Start writing from the 2nd element in counts
            row += 1

    # Merge cells for the last location
        if last_location_name is not None:
            worksheet.merge_range(location_start_row, 0, row - 1, 0, last_location_name)

    def _create_container_TAT_by_shipping_line(self, workbook):
        """Create a worksheet for the Container TAT report, grouped by shipping line."""

        worksheet = workbook.add_worksheet('Group By - Shipping Line')

        headers = ['Shipping Line', 'Location', 'Container Count', 'Average TAT', 
                'Same Day', '1 to 3 Days', '4 to 7 Days', '08 to 15 Days', '16 to 30 Days',
                '31 to 60 Days', '61 to 90 Days', '91 to 180 Days', 'Greater than 180 Days']

        header_format = workbook.add_format({
            'font_color': 'black',
            'bold': True,
            'border': 1,
        })

        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, header_format)

        row = 1
        last_shipping_line_name = None
        shipping_line_start_row = None
        domain = [('location_id', 'in', self.location_ids.ids), ('active', '=', False), ('move_out_date','<=', self.as_on_date)]

        # Get all the containers that match the relevant locations and shipping lines
        if self.shipping_line_ids:
            master_record = self.env['container.master'].search([('shipping_line_id', 'in', self.shipping_line_ids.ids)]).mapped('name')
            domain.append(('name', 'in', master_record))
        
        inventory_record = self.env['container.inventory'].search(domain)

        # Group by shipping line, and within each shipping line, group by location
        grouped_counts = defaultdict(lambda: defaultdict(lambda: [0] * len(headers[3:])))
        total_tat_days_by_shipping_line = {}

        for container in inventory_record:
            location = container.location_id.name
            shipping_line = container.container_master_id.shipping_line_id.name

            # Calculate TAT for each container
            if container.move_in_date and container.move_out_date:
                tat_days = (container.move_out_date - container.move_in_date).days

                # Initialize counters for each category
                tat_categories = {
                    'same_day': 0,
                    '1_to_3_days': 0,
                    '4_to_7_days': 0,
                    '8_to_15_days': 0,
                    '16_to_30_days': 0,
                    '31_to_60_days': 0,
                    '61_to_90_days': 0,
                    '91_to_180_days': 0,
                    'greater_than_180_days': 0
                }

                # Categorize the TAT days
                if tat_days == 0:
                    tat_categories['same_day'] += 1
                elif 1 <= tat_days <= 3:
                    tat_categories['1_to_3_days'] += 1
                elif 4 <= tat_days <= 7:
                    tat_categories['4_to_7_days'] += 1
                elif 8 <= tat_days <= 15:
                    tat_categories['8_to_15_days'] += 1
                elif 16 <= tat_days <= 30:
                    tat_categories['16_to_30_days'] += 1
                elif 31 <= tat_days <= 60:
                    tat_categories['31_to_60_days'] += 1
                elif 61 <= tat_days <= 90:
                    tat_categories['61_to_90_days'] += 1
                elif 91 <= tat_days <= 180:
                    tat_categories['91_to_180_days'] += 1
                else:
                    tat_categories['greater_than_180_days'] += 1

                # Update grouped counts
                tat_counts = grouped_counts[shipping_line][location]
                tat_counts[0] += 1  # Container count
                for idx, category in enumerate(tat_categories.values(), 1):  # Start from index 1
                    tat_counts[idx] += category

                # Track the total TAT days for each shipping line
                if shipping_line not in total_tat_days_by_shipping_line:
                    total_tat_days_by_shipping_line[shipping_line] = 0

                total_tat_days_by_shipping_line[shipping_line] += tat_days

        # Write data to the worksheet
        for shipping_line, locations in sorted(grouped_counts.items()):
            total_tat = total_tat_days_by_shipping_line[shipping_line]
            for location, counts in sorted(locations.items()):
                container_count = counts[0]
                average_tat = total_tat / container_count if container_count > 0 else 0

                if shipping_line != last_shipping_line_name:
                    if last_shipping_line_name is not None:
                        worksheet.merge_range(shipping_line_start_row, 0, row - 1, 0, last_shipping_line_name)

                    last_shipping_line_name = shipping_line
                    shipping_line_start_row = row

                worksheet.write(row, 0, shipping_line)  # Shipping Line
                worksheet.write(row, 1, location)  # Location
                worksheet.write(row, 2, container_count)  # Container Count
                worksheet.write(row, 3, round(average_tat, 2))  # Average TAT
                for i in range(9):  # Write TAT categories from columns 4 to 12
                    worksheet.write(row, i + 4, counts[i + 1])  # Start writing from the 2nd element in counts
                row += 1

        # Merge cells for the last shipping line
        if last_shipping_line_name is not None:
            worksheet.merge_range(shipping_line_start_row, 0, row - 1, 0, last_shipping_line_name)
