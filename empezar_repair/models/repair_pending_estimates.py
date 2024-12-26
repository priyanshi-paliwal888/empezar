import paramiko
import pytz
import base64
import re
from datetime import datetime
from odoo import fields, models, api, exceptions, _
from odoo.exceptions import ValidationError
from odoo.addons.empezar_base.models.res_users import ResUsers


class RepairPendingEstimates(models.Model):
    _name = "repair.pending.estimates"
    _description = "Repair Pending Estimates"
    _rec_name = "estimate_number"

    estimate_number = fields.Char(string="Estimate Number")
    pending_id = fields.Many2one("repair.pending", string="Pending ID")
    inventory_id = fields.Many2one('container.inventory', string="Container Inventory")
    estimate_line_ids = fields.One2many("repair.pending.estimates.lines","estimate_id", string="Pending Estimates Lines")
    container_no = fields.Char(string="Container No.", size=11, related="pending_id.container_no")
    type_size_id = fields.Many2one("container.size.type", string="Type/Size", related="pending_id.type_size_id")
    shipping_line_id = fields.Many2one(
        "res.partner",
        string="Shipping Line",
        domain="[('is_shipping_line', '=', True)]",
        related="pending_id.shipping_line_id",
    )
    shipping_line_logo = fields.Binary(
            string="Shipping Line", related="shipping_line_id.logo"
        )
    location_id = fields.Many2one('res.company', related="pending_id.location_id", string="Location")
    gross_wt = fields.Char(string="Gross Wt. (KG)", size=12, related="pending_id.gross_wt")
    tare_wt = fields.Char(string="Tare Wt. (KG)", size=12, related="pending_id.tare_wt")
    grade = fields.Selection([
        ('a', 'A'),
        ('b', 'B'),
        ('c', 'C')],
        string="Grade", required=True, related="pending_id.grade")
    damage_condition = fields.Many2one('damage.condition', string="Damage",
                                       required=True, related="pending_id.damage_condition")
    month = fields.Selection(
        [
            ("01", "January"),
            ("02", "February"),
            ("03", "March"),
            ("04", "April"),
            ("05", "May"),
            ("06", "June"),
            ("07", "July"),
            ("08", "August"),
            ("09", "September"),
            ("10", "October"),
            ("11", "November"),
            ("12", "December"),
        ],
        related="pending_id.month",
    )
    year = fields.Selection(related="pending_id.year")
    pre_repair_image_ids = fields.Many2many('ir.attachment', 'repair_estimates_pre_repair_rel'
                                            'repair_id','attachment_id', string="Add Images")
    pre_repair_date_and_time = fields.Datetime(string="Pre Repair Date/Time", default=fields.Datetime.now)
    post_repair_image_ids = fields.Many2many('ir.attachment','repair_estimates_post_repair_rel'
                                             'repair_id', 'attachment_id', string="Add Images")
    post_repair_date_and_time = fields.Datetime(string="Repair Completion Date/Time", default=fields.Datetime.now)
    is_send_to_shipping_line =  fields.Selection([("yes", "Yes"), ("no", "No")], string="Do you want to share with the Shipping Line?")
    is_send_post_repair_images = fields.Selection([("yes", "Yes"), ("no", "No")], string="Do you want to share with the Shipping Line?")
    total_amount= fields.Integer(string="Total", compute="compute_total_amount")
    total_amount_by_shipping_line = fields.Integer(string="Total By Shipping Line", compute="compute_total_amount_by_shipping_line")
    total_tax = fields.Integer(string="Total Tax", compute="compute_total_tax")
    total_tax_by_shipping_line = fields.Integer(string="Total Tax By Shipping Line", compute="compute_total_tax_by_shipping_line")
    grand_total = fields.Integer(string="Grand Total", compute="compute_grand_total")
    grand_total_by_shipping_line = fields.Integer(string="Grand Total By Shipping Line", compute="compute_grand_total_by_shipping_line")
    estimate_date_and_time = fields.Datetime(string="Estimate D/T", default=fields.Datetime.now)
    estimate_details = fields.Char(string="Estimate Details")
    repair_status = fields.Selection([
        ('awaiting_estimates', 'Awaiting Estimates'),
        ('awaiting_approval', 'Awaiting Approval'),
        ('approved', 'Approved'),
        ('partially_approved', 'Partially Approved'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected')
    ], string="Repair Status", default="awaiting_estimates", related="pending_id.repair_status")
    currency_id = fields.Many2one("res.currency",related='location_id.currency_id')
    display_create_info = fields.Char(compute="_get_create_record_info")
    display_modified_info = fields.Char(compute="_get_modify_record_info")
    attachment_id = fields.Many2one('ir.attachment', string="EDI Attachment")
    repair_completion_attachment_id = fields.Many2one('ir.attachment', string="Repair Completion Attachment")

    @api.depends('estimate_line_ids.total')
    def compute_total_amount(self):
        """Method to compute the total amount."""

        for rec in self:
            rec.total_amount = sum(rec.estimate_line_ids.mapped('total'))

    @api.depends('estimate_line_ids')
    def compute_total_amount_by_shipping_line(self):
        """Method to compute the total amount by shipping line."""

        for rec in self:
            rec.total_amount_by_shipping_line = sum(rec.estimate_line_ids.mapped('total_by_shipping_line'))

    @api.depends('total_amount')
    def compute_total_tax(self):
        """Method to compute the total tax."""

        for rec in self:
            rec.total_tax = rec.total_amount * 0.18

    @api.depends('total_amount_by_shipping_line')
    def compute_total_tax_by_shipping_line(self):
        """Method to compute the total tax by shipping line."""

        for rec in self:
            rec.total_tax_by_shipping_line = rec.total_amount_by_shipping_line * 0.18

    @api.depends('total_amount', 'total_tax')
    def compute_grand_total(self):
        """Method to compute the grand total."""

        for rec in self:
            rec.grand_total = rec.total_amount + rec.total_tax

    @api.depends('total_amount_by_shipping_line', 'total_tax_by_shipping_line')
    def compute_grand_total_by_shipping_line(self):
        """Method to compute the grand total by shipping line."""

        for rec in self:
            rec.grand_total_by_shipping_line = rec.total_amount_by_shipping_line + rec.total_tax_by_shipping_line

    def set_estimate_number(self):
        """Generate an estimate number based on the specified logic.
        """
        fixed_text = "EST"
        fiscal_year = 2324

        # Sequence number incremented each time an invoice is created
        sequence = self.env['ir.sequence'].next_by_code('repair.pending.estimate') or _("New")

        # Generate the invoice number
        estimate_number = f"{fixed_text}{fiscal_year}{sequence}"
        self.estimate_number = estimate_number
        return estimate_number

    @api.depends('container_no')
    def _compute_display_name(self):
        """Computes and sets the display name based on the container's name and company size type code."""
        for record in self:
            if record.container_no:
                if record.pending_id.type_size_id.company_size_type_code:
                    record.display_name = f'{record.container_no}({record.pending_id.type_size_id.company_size_type_code})'
                else:
                    record.display_name = record.container_no
            else:
                record.display_name = False

    @api.onchange("pre_repair_image_ids","post_repair_image_ids")
    @api.constrains("pre_repair_image_ids","post_repair_image_ids")
    def _check_pre_repair_image_size(self):
        """Method to check the size of the pre-repair images."""

        max_size = 553755  # 5 MB in bytes
        for record in self.pre_repair_image_ids:
            if record.file_size > max_size:
                raise ValidationError(_(
                    "File size cannot exceed 5MB."
                ))
        for record in self.post_repair_image_ids:
            if record.file_size > max_size:
                raise ValidationError(_(
                    "File size cannot exceed 5MB."
                ))

    @api.constrains('pre_repair_image_ids','post_repair_image_ids')
    def _check_pre_repair_images(self):
        allowed_extensions = ['jpg', 'jpeg', 'png']  # Add more image formats if needed
        for record in self:
            for attachment in record.pre_repair_image_ids:
                if not attachment.mimetype or not any(
                    attachment.mimetype.endswith(ext) for ext in allowed_extensions
                ):
                    raise ValidationError(_(
                    "Please upload only .jpeg and .png file."
                ))
            for attachment in record.post_repair_image_ids:
                if not attachment.mimetype or not any(
                    attachment.mimetype.endswith(ext) for ext in allowed_extensions
                ):
                    raise ValidationError(_(
                    "Please upload only .jpeg and .png file."
                ))

    def _get_create_record_info(self):
        """
        Assign create record log string to the appropriate field.
        :return: none
        """
        for rec in self:
            if rec.env.user.tz and rec.create_uid:
                tz_create_date = ResUsers.convert_datetime_to_user_timezone(rec.env.user,
                                                                            rec.create_date)
                create_uid_name = rec.create_uid.name
                if tz_create_date:
                    rec.display_create_info = ResUsers.get_user_log_data(rec, tz_create_date,
                                                                        create_uid_name)
            else:
                rec.display_create_info = ''

    def _get_modify_record_info(self):
        """
            Assign update record log string to the appropriate field.
            :return: none
        """
        for rec in self:
            if self.env.user.tz and rec.write_uid:
                tz_write_date = ResUsers.convert_datetime_to_user_timezone(rec.env.user,
                                                                        rec.write_date)
                write_uid_name = rec.write_uid.name
                if tz_write_date:
                    rec.display_modified_info = ResUsers.get_user_log_data(rec, tz_write_date,
                                                                        write_uid_name)
            else:
                rec.display_modified_info = ''
    
    def get_formatted_datetime(self, datetime_obj):
        """Returns the formatted date and time based on company settings."""
        get_company = self.env['res.company'].search(
                    [('parent_id', '=', False), ('active', '=', True)], limit=1)
        company_format = get_company.date_format

        # Define date formats
        date_formats = {
            'DD/MM/YYYY': '%d/%m/%Y %I:%M %p',
            'YYYY/MM/DD': '%Y/%m/%d %I:%M %p',
            'MM/DD/YYYY': '%m/%d/%Y %I:%M %p'
        }
        ist_timezone = pytz.timezone('Asia/Kolkata')
        local_date_time = datetime_obj.replace(tzinfo=pytz.utc)
        dt_ist = local_date_time.astimezone(ist_timezone)

        # Return the formatted date based on the company setting
        return dt_ist.strftime(date_formats.get(company_format, '%d/%m/%Y %I:%M %p'))
    
    def repair_completion_validation(self):
        """Method to validate the repair completion."""

        if self.estimate_date_and_time > self.post_repair_date_and_time:
            raise ValidationError(_("Please enter an Repair Completion Date/Time greater than Estimate Date/Time."))

    def action_send_to_shipping_line(self):
        """Method to send the estimate to the shipping line."""

        if not any(self.estimate_line_ids.mapped('description')):
            raise exceptions.UserError("There are no damages added for the container.")

        if self.pending_id.move_in_date_time and self.pending_id.move_in_date_time > self.estimate_date_and_time:
            raise ValidationError(_("Please enter an Estimate Date/Time greater than the Move In Date/Time."))

        if self.repair_status not in ['awaiting_estimates']:
            return {
                'name': 'WESTIM already sent',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'shipping.line.confirmation.wizard',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {
                    'default_pending_id': self.pending_id.id,
                }
            }
        self.send_westim_edi()
        if self.is_send_to_shipping_line == 'yes':
            for image in self.pre_repair_image_ids:
                self.send_image_via_ftp(image)
        return True

    def send_westim_edi(self):
        # Generate the EDI file content
        container_inventory = self.env['container.inventory'].search([('name', '=', self.container_no)],limit=1)
        data, estimate_number = self.generate_edi_file()
        estimate_date_and_time = self.get_formatted_datetime(self.estimate_date_and_time)
        if data:
            self.send_file_via_ftp(data)
            estimate_details = f"{estimate_number}  {estimate_date_and_time}"
            self.pending_id.write({
                'estimate_details': estimate_details,
                'repair_status': "awaiting_approval",
            })
            container_inventory.write({
                'status': 'aa',

            })

    # Helper function to convert datetime to user timezone and format it
    def format_datetime(self, dt, format_str='%d%m%y%H%M'):
        user_tz = self.env.user.tz or 'UTC'
        user_timezone = pytz.timezone(user_tz)
        user_time = dt.astimezone(user_timezone)
        return user_time.strftime(format_str)

    # Placeholder mapping for dynamic data
    def get_header_dynamic_value(self, placeholder_name):

        """
        Fetches the value of a dynamic placeholder from the record.
        Handles special placeholders or maps fields correctly.
        """
        # Define dictionary to map placeholders to functions or lambda expressions
        placeholder_map = {
            'reference_number1': lambda: '{reference_number1}',
            'reference_number2': lambda: '{reference_number2}',
            'depot_code(m&r)': lambda: self.location_id.shipping_line_mapping_ids.filtered(
                    lambda a: a.shipping_line_id == self.shipping_line_id
                )[:1].depot_code or 'UNKNOWN',
            'repair_vendor_code(m&r)': lambda: self.location_id.shipping_line_mapping_ids.filtered(
                    lambda a: a.shipping_line_id == self.shipping_line_id
                )[:1].repair_vendor_code or 'UNKNOWN',
            'date1': lambda: self.format_datetime(datetime.utcnow(), '%y%m%d'),
            'time1': lambda: self.format_datetime(datetime.utcnow(), '%H%M'),
            'date2': lambda: self.format_datetime(self.estimate_date_and_time, '%y%m%d'),
            'time2': lambda: self.format_datetime(self.estimate_date_and_time, '%H%M'),
            'date3': lambda: (
                self.format_datetime(self.pending_id.move_in_date_time,
                                     '%y%m%d') if self.pending_id.move_in_date_time else 'NA'
            ),
            'time3': lambda: (
                self.format_datetime(self.pending_id.move_in_date_time,
                                     '%H%M') if self.pending_id.move_in_date_time else 'NA'
            ),
            'labour_rate': lambda: (self.location_id.shipping_line_mapping_ids.filtered(
                lambda rec: rec.shipping_line_id == self.shipping_line_id
            )[:1].labour_rate) if self.location_id and self.shipping_line_id else 'NA',
            'container_number': lambda: self.container_no or 'NA',
            'type_size': lambda: 'ISO50',
            'gross_weight': lambda: self.gross_wt or 'NA',
            'production_year_month': lambda: (
                self.month+self.year[2:] if self.month and self.year else 'NA'
            )
        }
        # Get and execute the appropriate function or return 'UNKNOWN' if not found
        return placeholder_map.get(placeholder_name.lower(), lambda: 'UNKNOWN')()

    def get_footer_dynamic_value(self, placeholder_name):
        """
        Fetches the value of a dynamic placeholder from the record.
        Handles special placeholders or maps fields correctly.
        """
        # Define dictionary to map placeholders to functions or lambda expressions
        placeholder_map = {
            'tax_total': lambda: self.total_tax or 0,
            'total_estimate_cost': lambda: self.grand_total or 0,
            'line_count': lambda: str(16 + (3*len(self.estimate_line_ids))) if self.estimate_line_ids and self.estimate_line_ids[0].damage_type else
                        str(15 + (4*len(self.estimate_line_ids))) if self.estimate_line_ids and self.estimate_line_ids[0].damage_type_text else
                        '18',
            'edi_file_unique_number': lambda: '{reference_number1}',
            'reference_number1': lambda: '{reference_number1}',
            'labour_cost_total': lambda: sum(
                self.estimate_line_ids.mapped('labour_cost')) if self.estimate_line_ids else 'NA',
            'material_cost_total': lambda: sum(
                self.estimate_line_ids.mapped('material_cost')) if self.estimate_line_ids else 'NA',
        }
        # Get and execute the appropriate function or return 'UNKNOWN' if not found
        return placeholder_map.get(placeholder_name.lower(), lambda: 'UNKNOWN')()

    def get_body_dynamic_value(self, placeholder_name, estimate_line):
        """
        Fetches the value of a dynamic placeholder from the record.
        Handles special placeholders or maps fields correctly.
        """
        # Define dictionary to map placeholders to functions or lambda expressions
        placeholder_map = {
            'count': lambda: '{count}',
            'damage_location_code': lambda: (
                estimate_line.damage_location_id.damage_location if estimate_line else 'NA'
            ),
            'component_code': lambda: (
                estimate_line.component.code if estimate_line else 'NA'
            ),
            'damage_type_code': lambda: (
                estimate_line.damage_type.damage_type_code if estimate_line else 'NA'
            ),
            'material_type_code': lambda: (
                estimate_line.material_type.code if estimate_line else 'NA'
            ),
            'repair_type_code': lambda: (
                estimate_line.repair_type.repair_type_code if estimate_line else 'NA'
            ),
            'damage_location_code_text': lambda: (
                estimate_line.repair_code if estimate_line else 'NA'
            ),
            'component_code_text': lambda: (
                estimate_line.component_text if estimate_line else 'NA'
            ),
            'damage_type_code_text': lambda: (
                estimate_line.damage_type_text if estimate_line else 'NA'
            ),
            'material_type_code_text': lambda: (
                estimate_line.material_type_text if estimate_line else 'NA'
            ),
            'repair_type_code_text': lambda: (
                estimate_line.repair_code if estimate_line else 'NA'
            ),
            'uom': lambda: (
                estimate_line.measurement.name if estimate_line else 'NA'
            ),
            'length': lambda: (
                estimate_line.limit_id.limit if estimate_line.key_value.name == 'LN' and estimate_line.limit_id else
                estimate_line.limit_id.limit.split('*')[0] if estimate_line.key_value.name == 'LN*W' and estimate_line.limit_id else
                estimate_line.limit_id.limit.split('*')[0] if estimate_line.key_value.name == 'LN*W*H' and estimate_line.limit_id else
                ''
            ),
            'width': lambda: (
                estimate_line.limit_id.limit.split('*')[1] if estimate_line.key_value.name == 'LN*W' and estimate_line.limit_id else
                estimate_line.limit_id.limit.split('*')[0] if estimate_line.key_value.name == 'LN*W*H' and estimate_line.limit_id else
                ''
            ),
            'length_text': lambda: (
                estimate_line.limit_text if estimate_line.key_value.name == 'LN' else
                estimate_line.limit_text.split('*')[0] if estimate_line.key_value.name == 'LN*W' else
                estimate_line.limit_text.split('*')[0] if estimate_line.key_value.name == 'LN*W*H' else
                ''
            ),
            'width_text': lambda: (
                estimate_line.limit_text.split('*')[1] if estimate_line.key_value.name == 'LN*W' else
                estimate_line.limit_text.split('*')[1] if estimate_line.key_value.name == 'LN*W*H' else
                ''
            ),
            'height_text': lambda: (
                estimate_line.limit_text.split('*')[2] if estimate_line.key_value.name == 'LN*W*H' else
                ''
            ),
            'quantity': lambda: (
                estimate_line.qty if estimate_line else 'NA'
            ),
            'material_cost': lambda: (
                estimate_line.material_cost if estimate_line else 'NA'
            ),
            'total_material_cost': lambda: (
                estimate_line.material_cost if estimate_line else 'NA'
            ),
            'labour_rate': lambda: (self.location_id.shipping_line_mapping_ids.filtered(
                lambda rec: rec.shipping_line_id == self.shipping_line_id
            )[:1].labour_rate) if self.location_id and self.shipping_line_id else 'NA',
            'part_no': lambda: (
                estimate_line.part_no if estimate_line else ''
            ),
            'labour_hours*quantity': lambda: (
                int(estimate_line.qty)*int(estimate_line.labour_hour_text) if estimate_line.qty and estimate_line.labour_hour_text else ''
            ),
            'old_serial_number': lambda: (
                estimate_line.old_serial_no if estimate_line else ''
            ),
            'new_serial_number': lambda: (
                estimate_line.new_serial_no if estimate_line else ''
            ),
        }
        # Get and execute the appropriate function or return 'UNKNOWN' if not found
        return placeholder_map.get(placeholder_name.lower(), lambda: 'UNKNOWN')()

    def get_repair_completion_dynamic_value(self, placeholder_name):
        """
        Fetches the value of a dynamic placeholder from the record.
        Handles special placeholders or maps fields correctly.
        """
        # Define dictionary to map placeholders to functions or lambda expressions
        placeholder_map = {
            'vendor_code': lambda: self.location_id.shipping_line_mapping_ids.filtered(
                    lambda a: a.shipping_line_id == self.shipping_line_id
                )[:1].repair_vendor_code or 'UNKNOWN',
            'edi_file_creation_date': lambda: self.format_datetime(datetime.utcnow(), '%y%m%d'),
            'edi_file_creation_time': lambda: self.format_datetime(datetime.utcnow(), '%H%M'),
            'edi_file_unique_number': lambda: '{edi_file_unique_number}',
            'reference_number': lambda: '{reference_number}',
            'repair_completion_date': lambda: self.format_datetime(self.post_repair_date_and_time, '%y%m%d'),
            'estimates_creation_date': lambda: self.format_datetime(self.estimate_date_and_time, '%y%m%d'),
            'container_number': lambda: self.pending_id.container_no,
            'size_type_code': lambda: self.pending_id.type_size_id.company_size_type_code,
            'line_count': lambda: '10',
            'container_count': lambda: '1',
        }
        # Get and execute the appropriate function or return 'UNKNOWN' if not found
        return placeholder_map.get(placeholder_name.lower(), lambda: 'UNKNOWN')()

    def replace_placeholders(self, text, format_text, estimate_line=None):
        """
        Replace dynamic placeholders in the given text using the record's data.
        """
        # Find all placeholders in the format {placeholder}
        placeholders = re.findall(r'{(.*?)}', text)

        # Replace each placeholder with the corresponding record value
        for placeholder in placeholders:
            if format_text == 'body':
                value = self.get_body_dynamic_value(placeholder, estimate_line)
            elif format_text == 'header':
                value = self.get_header_dynamic_value(placeholder)
            elif format_text == 'completion':
                value = self.get_repair_completion_dynamic_value(placeholder)
            else:
                value = self.get_footer_dynamic_value(placeholder)
            text = text.replace(f'{{{placeholder}}}', str(value))  # Replace with actual value

        return text.strip()  # No need to strip HTML now

    def generate_edi_file(self):
        """
        Generates an EDI file based on Header, Body, Footer formats and
        dynamically replaces placeholders with record data.
        """
        if self:
            is_refer = self.pending_id.type_size_id.is_refer
            if is_refer == 'no':
                get_edi_configuration = self.env['repair.edi.setting'].search([('is_dry_edi','=',True)],limit=1)
            else:
                get_edi_configuration = self.env['repair.edi.setting'].search([('is_dry_edi', '=', False),
                                                                               ('is_repair_completion','=',False)],limit=1)

            # Extract EDI format parts
            header_text = get_edi_configuration.header
            body_text = get_edi_configuration.body
            footer_text = get_edi_configuration.footer

            # Prepare the header section (static, appears once)
            header_formatted = self.replace_placeholders(header_text, 'header')

            # Initialize the body content, which will be repeated for each record
            body_content = ''
            count = 1
            for rec in self.estimate_line_ids:
                # Dynamically replace placeholders for each record
                body_formatted = self.replace_placeholders(body_text, 'body', rec)
                body_formatted = body_formatted.replace('{count}', str(count))
                body_content += body_formatted + '\n'
                count += 1

            # Prepare the footer section (static, appears once)
            footer_formatted = self.replace_placeholders(footer_text, 'footer')

            # Generate the sequence number only once if needed
            if not self.pending_id.estimate_details:
                estimate_number = self.set_estimate_number()
            else:
                estimate_number = self.pending_id.estimate_details.split(' ')[0]
            # Replace the "Reference Number 1" placeholder in all relevant sections
            header_formatted = header_formatted.replace('{reference_number2}', estimate_number)
            footer_formatted = footer_formatted.replace('{reference_number2}', estimate_number)

            # Generate the sequence number only once if needed
            ref_number_1 = self.env['ir.sequence'].next_by_code('repair.pending.edi.ref')
            # Replace the "Reference Number 1" placeholder in all relevant sections
            header_formatted = header_formatted.replace('{reference_number1}', ref_number_1)
            footer_formatted = footer_formatted.replace('{reference_number1}', ref_number_1)

            # Combine all parts into the final EDI content
            edi_content = f"{header_formatted}\n{body_content}{footer_formatted}"

            repair_vendor_code = self.get_header_dynamic_value('repair_vendor_code(m&r)')
            container_number = self.pending_id.container_no
            new_file_name = '%s_%s_%s.edi' % (repair_vendor_code, estimate_number, container_number)

            # Remove any existing attachments with the same name
            existing_attachments = self.env['ir.attachment'].sudo().search([('name', '=', new_file_name)])
            for attach in existing_attachments:
                attach.sudo().unlink()

            # Save the EDI content as an attachment
            attachment = self.env['ir.attachment'].create({
                'name': new_file_name,
                'datas': base64.b64encode(edi_content.encode('utf-8')),
                'public': True,
                'type': 'binary',
                'mimetype': 'text/plain',  # Ensure this is set to plain text
            })
            self.attachment_id =  attachment
            return attachment, estimate_number
        return False

    def send_file_via_ftp(self, data):
        """
        Send edi file via sftp.
        """
        location = self.location_id
        shipping_line_id = self.shipping_line_id
        if location and shipping_line_id:
            get_mapped_shipping_line = location.shipping_line_mapping_ids.filtered(
                lambda rec: rec.shipping_line_id == shipping_line_id
            )[:1]
            if get_mapped_shipping_line and get_mapped_shipping_line.repair == 'yes':
                ftp_directory = get_mapped_shipping_line.folder_name_westim
                ftp_ip = get_mapped_shipping_line.ftp_location
                username = get_mapped_shipping_line.ftp_username
                password = get_mapped_shipping_line.ftp_password
                port_number = get_mapped_shipping_line.port_number
        else:
            ftp_directory = ''
            ftp_ip = ''
            username = ''
            password = ''
            port_number = ''

        # Decode the base64 data to get the actual file content
        file_content = base64.b64decode(data.datas)
        file_name = data.name

        try:
            # Establish SFTP connection using paramiko
            transport = paramiko.Transport((ftp_ip, port_number))
            transport.connect(username=username, password=password)

            # Start SFTP session
            sftp = paramiko.SFTPClient.from_transport(transport)

            # Create a full path for the file to be uploaded
            remote_file_path = f'{ftp_directory}/{file_name}'

            # Write the file to the FTP server
            with sftp.file(remote_file_path, 'wb') as remote_file:
                remote_file.write(file_content)

            # Close the connection
            sftp.close()
            transport.close()

        except Exception as e:
            raise ValidationError('Failed to upload file via SFTP: %s' % e)

    def send_image_via_ftp(self, data):
        """
        Send an image file via SFTP.
        """
        location = self.location_id
        shipping_line_id = self.shipping_line_id
        if location and shipping_line_id:
            get_mapped_shipping_line = location.shipping_line_mapping_ids.filtered(
                lambda rec: rec.shipping_line_id == shipping_line_id
            )[:1]
            if get_mapped_shipping_line and get_mapped_shipping_line.repair == 'yes':
                ftp_directory = get_mapped_shipping_line.folder_name_before_images
                ftp_ip = get_mapped_shipping_line.ftp_location
                username = get_mapped_shipping_line.ftp_username
                password = get_mapped_shipping_line.ftp_password
                port_number = get_mapped_shipping_line.port_number
            else:
                raise ValidationError("No valid FTP configuration found.")
        else:
            raise ValidationError("Location or shipping line is missing.")

        # Decode the base64 data to get the actual image file content
        try:
            file_content = base64.b64decode(data.datas)
            file_name = data.name
        except Exception as decode_error:
            raise ValidationError(f"Failed to decode file content: {decode_error}")

        # Check if the file has an image extension
        if not file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            raise ValidationError("The provided file is not a valid image format.")

        try:
            # Establish SFTP connection using paramiko
            transport = paramiko.Transport((ftp_ip, int(port_number)))
            transport.connect(username=username, password=password)

            # Start SFTP session
            sftp = paramiko.SFTPClient.from_transport(transport)

            # Create a full path for the file to be uploaded
            remote_file_path = f'{ftp_directory}/{file_name}'

            # Write the file to the FTP server
            with sftp.file(remote_file_path, 'wb') as remote_file:
                remote_file.write(file_content)

            # Close the connection
            sftp.close()
            transport.close()

        except Exception as e:
            raise ValidationError(f"Failed to upload file via SFTP: {e}")

    def send_repair_completion_file_via_ftp(self, data):
        """
        Send edi file via sftp.
        """
        location = self.location_id
        shipping_line_id = self.shipping_line_id
        if location and shipping_line_id:
            get_mapped_shipping_line = location.shipping_line_mapping_ids.filtered(
                lambda rec: rec.shipping_line_id == shipping_line_id
            )[:1]
            if get_mapped_shipping_line and get_mapped_shipping_line.repair == 'yes':
                ftp_directory = get_mapped_shipping_line.folder_name_destim_response
                ftp_ip = get_mapped_shipping_line.ftp_location
                username = get_mapped_shipping_line.ftp_username
                password = get_mapped_shipping_line.ftp_password
                port_number = get_mapped_shipping_line.port_number
        else:
            ftp_directory = ''
            ftp_ip = ''
            username = ''
            password = ''
            port_number = ''

        # Decode the base64 data to get the actual file content
        file_content = base64.b64decode(data.datas)
        file_name = data.name

        try:
            # Establish SFTP connection using paramiko
            transport = paramiko.Transport((ftp_ip, port_number))
            transport.connect(username=username, password=password)

            # Start SFTP session
            sftp = paramiko.SFTPClient.from_transport(transport)

            # Create a full path for the file to be uploaded
            remote_file_path = f'{ftp_directory}/{file_name}'

            # Write the file to the FTP server
            with sftp.file(remote_file_path, 'wb') as remote_file:
                remote_file.write(file_content)

            # Close the connection
            sftp.close()
            transport.close()

        except Exception as e:
            raise ValidationError('Failed to upload file via SFTP: %s' % e)

    def generate_repair_completion_edi(self):
        """
                Generates an EDI file based on Header, Body, Footer formats and
                dynamically replaces placeholders with record data.
                """
        if self:
            get_edi_configuration = self.env['repair.edi.setting'].search([('is_repair_completion', '=', True)],limit=1)

            # Extract EDI format parts
            body_text = get_edi_configuration.body

            body_formatted = self.replace_placeholders(body_text, 'completion')

            estimate_number = self.pending_id.estimate_details.split(' ')[0]

            # Generate the sequence number only once if needed
            ref_number_1 = self.env['ir.sequence'].next_by_code('repair.pending.edi.ref')
            body_formatted = body_formatted.replace('{edi_file_unique_number}', ref_number_1)
            body_formatted = body_formatted.replace('{reference_number}', estimate_number)

            # Combine all parts into the final EDI content
            edi_content = f"{body_formatted}"

            repair_vendor_code = self.get_header_dynamic_value('repair_vendor_code(m&r)')
            container_number = self.pending_id.container_no
            new_file_name = '%s_%s_%s.edi' % (repair_vendor_code, estimate_number, container_number)

            # Remove any existing attachments with the same name
            existing_attachments = self.env['ir.attachment'].sudo().search([('name', '=', new_file_name)])
            for attach in existing_attachments:
                attach.sudo().unlink()

            # Save the EDI content as an attachment
            attachment = self.env['ir.attachment'].create({
                'name': new_file_name,
                'datas': base64.b64encode(edi_content.encode('utf-8')),
                'public': True,
                'type': 'binary',
                'mimetype': 'text/plain',  # Ensure this is set to plain text
            })
            self.repair_completion_attachment_id = attachment.id
            return attachment
        return False

    def download_repair_completion_edi_file(self):
        """
        Method to download the EDI file attachment.
        """
        if self.repair_completion_attachment_id:
            attachment = self.repair_completion_attachment_id
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{attachment.id}?download=true',
                'target': 'self',
            }
        else:
            raise  ValidationError(_("No EDI file generated yet."))

    def send_repair_completion_image_via_ftp(self, data):
        """
        Send an image file via SFTP.
        """
        location = self.location_id
        shipping_line_id = self.shipping_line_id

        # Initialize FTP credentials and directory
        ftp_directory = ''
        ftp_ip = ''
        username = ''
        password = ''
        port_number = 22  # Default SFTP port

        if location and shipping_line_id:
            get_mapped_shipping_line = location.shipping_line_mapping_ids.filtered(
                lambda rec: rec.shipping_line_id == shipping_line_id
            )[:1]
            if get_mapped_shipping_line and get_mapped_shipping_line.repair == 'yes':
                ftp_directory = get_mapped_shipping_line.folder_name_after_images
                ftp_ip = get_mapped_shipping_line.ftp_location
                username = get_mapped_shipping_line.ftp_username
                password = get_mapped_shipping_line.ftp_password
                port_number = get_mapped_shipping_line.port_number or 22

        if not ftp_ip or not username or not ftp_directory:
            raise ValidationError("FTP configuration is incomplete. Please verify the settings.")

        # Decode the base64 data to get the actual image content
        try:
            image_content = base64.b64decode(data.datas)
            image_name = data.name
            if not image_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                raise ValidationError("The file is not a valid image format.")
        except Exception as decode_error:
            raise ValidationError("Failed to decode the image data: %s" % decode_error)

        try:
            # Establish SFTP connection using paramiko
            transport = paramiko.Transport((ftp_ip, port_number))
            transport.connect(username=username, password=password)

            # Start SFTP session
            sftp = paramiko.SFTPClient.from_transport(transport)

            # Create a full path for the file to be uploaded
            remote_file_path = f'{ftp_directory}/{image_name}'

            # Write the image file to the FTP server
            with sftp.file(remote_file_path, 'wb') as remote_file:
                remote_file.write(image_content)

            # Close the connection
            sftp.close()
            transport.close()

        except Exception as e:
            raise ValidationError('Failed to upload image via SFTP: %s' % e)

    def download_edi_file(self):
        """
        Method to download the EDI file attachment.
        """
        if self.attachment_id:
            attachment = self.attachment_id
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{attachment.id}?download=true',
                'target': 'self',
            }
        else:
            raise  ValidationError(_("No EDI file generated yet."))

    def action_repair_completion(self):
        """Method to complete the repair."""

        container_inventory = self.env['container.inventory'].search([('name', '=', self.container_no)])
        self.repair_completion_validation()
        edi_file = self.generate_repair_completion_edi()
        if edi_file:
            if self.is_send_post_repair_images == 'yes':
                for image in self.post_repair_image_ids:
                    self.send_repair_completion_image_via_ftp(image)
            self.send_repair_completion_file_via_ftp(edi_file)
            self.pending_id.write({"repair_status": "completed"})
            container_inventory.write({
                    'status': 'av',

                })
        return True
