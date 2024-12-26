import re
import paramiko
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from lxml import etree
from odoo.addons.empezar_base.models.res_users import ResUsers

class RepairPendingContainer(models.Model):
    _name = "repair.pending"
    _description = "Repair Pending"
    _rec_name = "display_name"

    def get_years(self):
        """Get years"""
        year_list = []
        for i in range(1950, 4000):
            year_list.append((str(i), str(i)))
        return year_list

    move_in_id = fields.Many2one('move.in', string="Move In Record")
    pending_ids = fields.One2many("repair.pending.estimates", "pending_id", string="Pending ID")
    location_id = fields.Many2one('res.company',string="Location", required=True)
    location_id_domain = fields.Char(string="Location Domain", compute="_compute_location_id_domain")
    is_location_editable = fields.Boolean(string="Is Location Editable", default=False)
    shipping_line_id = fields.Many2one(
        "res.partner",
        string="Shipping Line",
        domain="[('is_shipping_line', '=', True)]", required=True
    )
    shipping_line_id_domain = fields.Many2many('res.partner', compute='_compute_shipping_line_id_domain')
    shipping_line_logo = fields.Binary(string="Shipping Line", related="shipping_line_id.logo")
    container_no = fields.Char(string="Container Details", size=11, required=True)
    estimate_details = fields.Char(string="Estimate Details")
    move_in_date_time = fields.Datetime(string="Move In Date/Time")
    repair_status = fields.Selection([
        ('awaiting_estimates', 'Awaiting Estimates'),
        ('awaiting_approval', 'Awaiting Approval'),
        ('approved', 'Approved'),
        ('partially_approved', 'Partially Approved'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected')
    ], string="Repair Status", default="awaiting_estimates")
    grade = fields.Selection([
        ('a', 'A'),
        ('b', 'B'),
        ('c', 'C')],
        string="Grade", required=True)
    damage_condition = fields.Many2one('damage.condition', string="Damage",
                                       required=True)
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
        ]
    )
    year = fields.Selection(get_years)
    type_size_id = fields.Many2one("container.type.data", string="Type/Size", required=True)
    type_size_id_domain = fields.Char(string="Type/Size Domain", compute="_compute_type_size_id_domain")
    gross_wt = fields.Char(string="Gross Wt. (KG)", size=12, required=True)
    tare_wt = fields.Char(string="Tare Wt. (KG)", size=12, required=True)
    is_editable = fields.Boolean(string="Is Editable", compute="_compute_is_editable")
    estimate_date_and_time = fields.Datetime(string="Estimate Date", related="pending_ids.estimate_date_and_time")
    estimate_number = fields.Char(string="Estimate Reference No.", related="pending_ids.estimate_number")
    display_create_info = fields.Char(compute="_get_create_record_info")
    display_modified_info = fields.Char(compute="_get_modify_record_info")
    display_sources = fields.Char(string="Sources",readonly=True,compute="_compute_display_sources")

    @api.depends('shipping_line_id', 'location_id')
    def _compute_type_size_id_domain(self):
        for record in self:
            if record.shipping_line_id and record.location_id:
                # Fetch the `refer_container` value from the shipping line mapping for this location and shipping line
                mapping = self.env['location.shipping.line.mapping'].search([
                    ('shipping_line_id', '=', record.shipping_line_id.id),
                    ('company_id', '=', record.location_id.id)
                ], limit=1)
                if mapping:
                    if mapping.refer_container == 'yes':
                        record.type_size_id_domain = [('is_refer', '=', 'yes')]
                    elif mapping.refer_container == 'no':
                        record.type_size_id_domain = [('is_refer', '=', 'no')]
                else:
                    record.type_size_id_domain = []
            else:
                record.type_size_id_domain = []

    @api.onchange('container_no')
    def _onchange_container_no(self):
        """
        If the container exists in the 'container.master' model, populate the corresponding fields.
        Otherwise, allow the user to enter their own values.
        """

        container_master = self.env['container.master'].search([('name', '=', self.container_no)], limit=1)
        container_shipping_line_id = container_master.shipping_line_id
        for shipping_mapping in self.location_id.shipping_line_mapping_ids:
            if shipping_mapping.shipping_line_id.id == container_master.shipping_line_id.id:
                if shipping_mapping.repair == 'yes':
                    self.shipping_line_id = container_master.shipping_line_id.id
                    self.type_size_id = container_master.type_size.id if container_master.type_size else False
                    self.gross_wt = container_master.gross_wt
                    self.tare_wt = container_master.tare_wt
                    self.year = container_master.year
                    self.month = container_master.month

        mapping_shipping_line_obj = self.env['location.shipping.line.mapping'].search([
            ('company_id', '=', self.location_id.id),
            ('shipping_line_id', '=', container_shipping_line_id.id)
        ], limit=1)

        if not mapping_shipping_line_obj:
            return

    @api.constrains('container_no')
    def _check_container(self):
        """
        Check if the container exists in the container.master model.
        """

        container_master = self.env['container.master'].search([('name', '=', self.container_no)], limit=1)
        if not container_master and self.container_no :
                self.env['container.master'].create({
                    'name': self.container_no,
                    'shipping_line_id': self.shipping_line_id.id,
                    'type_size': self.type_size_id.id,
                    'month': self.month,
                    'year': self.year,
                    'gross_wt': self.gross_wt,
                    'tare_wt': self.tare_wt,
                })

    def _get_create_record_info(self):
        """
        Assign create record log string to the appropriate field.
        :return: none
        """
        for rec in self:
            if rec.env.user.tz and rec.create_uid:
                tz_create_date = ResUsers.convert_datetime_to_user_timezone(
                    rec.env.user, rec.create_date
                )
                create_uid_name = rec.create_uid.name
                if tz_create_date:
                    rec.display_create_info = ResUsers.get_user_log_data(
                        rec, tz_create_date, create_uid_name
                    )
            else:
                rec.display_create_info = ""

    def _get_modify_record_info(self):
        """
        Assign update record log string to the appropriate field.
        :return: none
        """
        for rec in self:
            if rec.env.user.tz and rec.write_uid:
                tz_write_date = ResUsers.convert_datetime_to_user_timezone(
                    rec.env.user, rec.write_date
                )
                write_uid_name = rec.write_uid.name
                if tz_write_date:
                    rec.display_modified_info = ResUsers.get_user_log_data(
                        rec, tz_write_date, write_uid_name
                    )
            else:
                rec.display_modified_info = ""

    def _compute_display_sources(self):
        """
        Assign Value while creating a record from an import file and Creating a custom Record
        """
        for record in self: 
            record.display_sources = 'System'

    @api.model
    def update_container_master(self, rec_container, rec_shipping_line=None, rec_type_size=None,
                                rec_production_month=None, rec_production_year=None,
                                rec_gross_weight=None, rec_tare_weight=None):
        """
        Update the container master record conditionally
        based on the provided inputs.
        """
        if not rec_container:
            return False  # Early return if no container is provided

        master_obj = self.env['container.master'].search([('name', '=', rec_container)], limit=1)

        if not master_obj:
            return False  # Early return if no matching master record is found

        # Create a dictionary of values to update based on the provided data
        vals = {
            'shipping_line_id': rec_shipping_line,
            'type_size': rec_type_size,
            'month': rec_production_month,
            'year': rec_production_year,
            'gross_wt': rec_gross_weight,
            'tare_wt': rec_tare_weight
        }

        # Remove any None values from vals to prevent unnecessary updates
        vals = {key: value for key, value in vals.items() if value}

        if vals:
            master_obj.write(vals)  # Update only if there are values to update

        return True

    @api.depends('location_id')
    def _compute_location_id_domain(self):
        """Compute location domain based on the repair operation."""

        for record in self:
            non_repair_companies = self.env['res.company'].search([('operations_ids.name', '!=', 'Repair')])
            repair_companies = self.env['res.company'].search([('operations_ids.name', '=', 'Repair'),('id', 'not in', non_repair_companies.ids)])
            user_companies = self.env.user.company_ids
            allowed_companies = repair_companies & user_companies
            record.location_id_domain = str([('id', 'in', allowed_companies.ids)])

    @api.depends('location_id')
    def _compute_shipping_line_id_domain(self):
        """Compute shipping line domain based on location and repair estimate.
        """
        for record in self:
            if record.location_id:
                # Fetch the shipping lines based on the location_id
                shipping_lines = self.env['location.shipping.line.mapping'].search([
                ('company_id', '=', record.location_id.id),
                ('repair', '=', 'yes')
                ]).mapped('shipping_line_id')
                record.shipping_line_id_domain = [(6, 0, shipping_lines.ids)]
            else:
                record.shipping_line_id_domain = []

    @api.model
    def default_get(self, fields):
        """ Override the default get method to set the selected record ids"""
        res = super().default_get(fields)
        if 'location_id' in fields:
            non_repair_companies = self.env['res.company'].search([('operations_ids.name', '!=', 'Repair')])
            repair_companies = self.env['res.company'].search([('operations_ids.name', '=', 'Repair'),('id', 'not in', non_repair_companies.ids)])
            user_companies = self.env.user.company_ids
            allowed_companies = repair_companies & user_companies
            if len(allowed_companies) == 1:
                res['location_id'] = allowed_companies[0].id
        return res

    def _compute_display_name(self):
        """Computes and sets the display name based on the container's name and company size type code."""
        for record in self:
            if record.container_no:
                if record.type_size_id.company_size_type_code:
                    record.display_name = f'{record.container_no}({record.type_size_id.company_size_type_code})'
                else:
                    record.display_name = record.container_no
            else:
                record.display_name = False

    @api.constrains('container_no')
    def _check_container_no_validations(self):
        """Check if the container number is valid."""
        for record in self:
            if len(record.container_no) != 11 :
                raise ValidationError("Container number should be 11 characters long.")
            container_regex = r'^[A-Za-z]{4}[0-9]{7}$'
            if not re.match(container_regex, record.container_no):
                raise ValidationError(_("Container Number is invalid."))
            char_to_num_dict = {
                    'A': 10, 'B': 12, 'C': 13, 'D': 14, 'E': 15, 'F': 16, 'G': 17, 'H': 18, 'I': 19,
                    'J': 20, 'K': 21, 'L': 23, 'M': 24, 'N': 25, 'O': 26, 'P': 27, 'Q': 28, 'R': 29,
                    'S': 30, 'T': 31, 'U': 32, 'V': 34, 'W': 35, 'X': 36, 'Y': 37, 'Z': 38
                }
            input_data = str(record.container_no).upper()
            sliced_input_data = input_data[:10]
            total_sum = sum(
                (char_to_num_dict.get(char) if char_to_num_dict.get(char) else int(char)) * (2 ** index)
                for index, char in enumerate(sliced_input_data)
            )
            rounded_division_result = (int(total_sum/11)) * 11
            remainder = total_sum - rounded_division_result
            new_digit = remainder % 10
            if new_digit != eval(record.container_no[-1]):
                raise ValidationError(_("Container Number is invalid."))

            mapping = self.env['location.shipping.line.mapping'].search([
                ('shipping_line_id', '=', record.shipping_line_id.id),
                ('company_id', '=', record.location_id.id)
            ], limit=1)

            if mapping and mapping.refer_container == 'yes':
                if record.type_size_id and record.type_size_id.is_refer == 'no':
                    raise ValidationError(_(f"No reefer containers are allowed to repaired at {self.location_id.name}."))

    @api.constrains('container_no')
    def _check_repair_status(self):
        for record in self:
            if record.container_no:
                existing_record = self.env['repair.pending'].search([
                    ('container_no', '=', record.container_no),
                    ('id', '!=', record.id), 
                    ('repair_status', 'not in', ['completed', 'rejected']),
                ], limit=1)
                if existing_record:
                    raise ValidationError(
                        _( "You cannot create or use this container number until the repair flow is completed for this container."))

    @api.constrains("gross_wt", "tare_wt")
    def _check_wt_validation(self):
        if self.gross_wt and self.tare_wt:
            if int(self.tare_wt) > int(self.gross_wt):
                raise ValidationError(
                    _("Tare Weight cannot be greater than Gross Weight")
                )
        if int(self.gross_wt) == 0:
            raise ValidationError(_("Gross Weight cannot be 0"))
        if int(self.tare_wt) == 0:
            raise ValidationError(_("Tare Weight cannot be 0"))

    @api.onchange('gross_wt', 'tare_wt')
    @api.constrains('gross_wt', 'tare_wt')
    def onchange_gross_and_tare_weight(self):
        """
        Tare weight and gross weight validations.
        """
        self.ensure_one()
        for weight_field in ['gross_wt', 'tare_wt']:
            weight_value = getattr(self, weight_field)
            if weight_value:
                if not weight_value.isdigit():
                    raise ValidationError(_('The {} must be integer.').format(
                        self._fields[weight_field].string))

                weight_value_int = int(weight_value)

                if weight_value_int < 0:
                    raise ValidationError(_('Negative weight is not allowed for {}.').format(
                        self._fields[weight_field].string))

    def action_add_estimate(self):
        """Add an estimate to the repair pending container."""
        existing_estimate = self.env['repair.pending.estimates'].search([
                            ('pending_id', '=', self.id) ], limit=1)
        if existing_estimate:
            return {
            'type': 'ir.actions.act_window',
            'name': 'Estimate Form',
            'res_model': 'repair.pending.estimates',
            'view_mode': 'form',
            'views': [(self.env.ref('empezar_repair.view_estimates_form').id, 'form')],
            'res_id': existing_estimate.id,
            'target': 'current',
            }
        return {
            'type': 'ir.actions.act_window',
            'name': 'Estimate Form',
            'res_model':  'repair.pending.estimates',
            'view_mode': 'form',
            'views': [(self.env.ref('empezar_repair.view_estimates_form').id, 'form')],
            'context': {'default_pending_id': self.id},
        }

    def action_edit_estimate(self):

        """Edit an estimate to the repair pending container."""
        existing_estimate = self.env['repair.pending.estimates'].search([
                            ('pending_id', '=', self.id) ], limit=1)
        if self.repair_status == 'approved':
            return {
                'type': 'ir.actions.act_window',
                'name': 'Edit Estimate',
                'res_model': 'edit.estimate.wizard',
                'view_mode': 'form',
                'target': 'new',
            }

        if existing_estimate:
            return {
            'type': 'ir.actions.act_window',
            'name': 'Estimate Form',
            'res_model': 'repair.pending.estimates',
            'view_mode': 'form',
            'views': [(self.env.ref('empezar_repair.view_estimates_form').id, 'form')],
            'res_id': existing_estimate.id,
            'target': 'current',
            }

    def action_view_estimate(self):
        """View an estimate to the repair pending container."""
        existing_estimate = self.env['repair.pending.estimates'].search([
                            ('pending_id', '=', self.id) ], limit=1)
        if existing_estimate:
            return {
            'type': 'ir.actions.act_window',
            'name': 'Estimate Form',
            'res_model': 'repair.pending.estimates',
            'view_mode': 'form',
            'views': [(self.env.ref('empezar_repair.view_estimates_page_form').id, 'form')],
            'res_id': existing_estimate.id,
            'target': 'current',
            }

    def action_repair_completion(self):
        """View the repair compeletion container."""
        existing_estimate = self.env['repair.pending.estimates'].search([
                            ('pending_id', '=', self.id) ], limit=1)
        if existing_estimate:
            return {
            'type': 'ir.actions.act_window',
            'name': 'Estimate Form',
            'res_model': 'repair.pending.estimates',
            'view_mode': 'form',
            'views': [(self.env.ref('empezar_repair.view_repair_completion_form').id, 'form')],
            'res_id': existing_estimate.id,
            'target': 'current',
            }

    def get_view(self, view_id=None, view_type='tree', **options):
        """Get the view based on the user's company."""

        res = super().get_view(view_id, view_type, **options)
        if view_type == 'tree':
            if res.get('model', '') in ['repair.pending']:
                user_locations = self.env.user.company_ids
                if len(user_locations) > 1:
                    return res
                if len(user_locations) == 1:
                    current_company = self.env.user.company_id
                    repair_operation = current_company.operations_ids.mapped('name')
                    if 'Gate Operations' in repair_operation:
                        doc = etree.XML(res['arch'])
                        for node in doc.xpath("//tree"):
                            node.set('create', 'false')
                        res['arch'] = etree.tostring(doc)
        return res

    @api.depends('location_id')
    def _compute_is_editable(self):
        for record in self:
            repair_operation = record.location_id.operations_ids.mapped('name')
            if 'Repair' in repair_operation and 'Gate Operations' in repair_operation:
                record.is_editable = False
            elif 'Repair' in repair_operation and 'Gate Operations' not in repair_operation and record.repair_status != 'awaiting_estimates':
                record.is_editable = False
            else:
                record.is_editable = True

    @staticmethod
    def extract_reference_number(file_content):
        """
        Extract the Reference_Number from the file content.
        """
        try:
            # Match the Reference_Number in Line 4 or Line 7
            match = re.search(r"BGM\+\d+\+(\w+)\+|RFF\+TES:(\w+)", file_content)
            if match:
                return match.group(1) or match.group(2)
            return None
        except Exception as e:
            print(f"Error extracting Reference_Number: {e}")
            return None

    @staticmethod
    def extract_damage_and_status(file_content):
        """
        Extract damage count and line item status from LIN lines in the file content.

        Args:
            file_content (str): The complete content of the file as a string.

        Returns:
            list: A list of dictionaries containing damage count and line item status.
        """
        try:
            # Regex pattern to capture Damage Count and Line Item Status from LIN lines
            lin_pattern = r"LIN\+(\d+)\+([\w\s]+)'"
            matches = re.findall(lin_pattern, file_content)

            # Create a list of dictionaries for better structure
            extracted_data = [
                {"damage_count": match[0], "line_item_status": match[1].strip()}
                for match in matches
            ]
            return extracted_data
        except Exception as e:
            print(f"Error while extracting data: {e}")
            return []

    def extract_line_data(self,file_content):
        """
        Extract line-specific data (MOA values) from the EDI file content.
        :param file_content: The string content of the file.
        :return: A list of dictionaries containing line-specific data.
        """
        line_pattern = r"(LIN\+\d+\+.*?)(?=LIN\+|\Z)"  # Regex to match each LIN block
        lines = re.findall(line_pattern, file_content, re.DOTALL)
        line_data = []

        for line in lines:
            labour_cost = None
            shipping_cost = None
            material_cost = None

            # Extract MOA values for the current line
            labour_match = re.search(r"MOA\+185:(\d+(\.\d+)?):INR", line)
            if labour_match:
                labour_cost = float(labour_match.group(1))

            shipping_match = re.search(r"MOA\+124:(\d+(\.\d+)?):INR", line)
            if shipping_match:
                shipping_cost = float(shipping_match.group(1))

            material_match = re.search(r"MOA\+186:(\d+(\.\d+)?):INR", line)
            if material_match:
                material_cost = float(material_match.group(1))

            line_data.append({
                "labour_cost": labour_cost,
                "shipping_cost": shipping_cost,
                "material_cost": material_cost,
            })

        return line_data

    def update_estimate_lines_records(self):
        """
        Establish SFTP connection, process files containing the container_no in their names,
        and update repair statuses based on the extracted file content.
        """
        location = self.location_id
        shipping_line_id = self.shipping_line_id
        if not location or not shipping_line_id:
            print("Location or shipping line is not set.")
            return False

        # Retrieve mapped shipping line configuration
        mapped_shipping_line = location.shipping_line_mapping_ids.filtered(
            lambda rec: rec.shipping_line_id == shipping_line_id and rec.repair == 'yes'
        )[:1]

        if not mapped_shipping_line:
            print("No valid shipping line mapping found.")
            return False

        container_no = self.container_no
        if not container_no:
            print("Container number is not defined.")
            return False

        # Extract SFTP details
        sftp_host = mapped_shipping_line.ftp_location
        sftp_port = mapped_shipping_line.port_number
        sftp_username = mapped_shipping_line.ftp_username
        sftp_password = mapped_shipping_line.ftp_password
        remote_directory = mapped_shipping_line.folder_name_destim

        try:
            # Establish SFTP connection using paramiko
            transport = paramiko.Transport((sftp_host, sftp_port))
            transport.connect(username=sftp_username, password=sftp_password)

            sftp = paramiko.SFTPClient.from_transport(transport)
            file_list = sftp.listdir(remote_directory)

            # Filter files containing the container_no in their names
            filtered_files = [file_name for file_name in file_list if container_no in file_name]
            if not filtered_files:
                print("No files found containing the container number.")
                sftp.close()
                return False

            results = []
            reference_number = None

            # Process each filtered file
            for file_name in filtered_files:
                remote_file_path = f"{remote_directory}/{file_name}"
                try:
                    with sftp.open(remote_file_path, 'r') as remote_file:
                        file_content = remote_file.read().decode('utf-8')
                    # Extract reference number and damage data
                    reference_number = RepairPendingContainer.extract_reference_number(file_content)
                    if reference_number and self.estimate_details:
                        repair_estimate_number = self.estimate_details.split(' ')[0]
                        if repair_estimate_number != reference_number:
                            continue
                    file_results = RepairPendingContainer.extract_damage_and_status(file_content)
                    if file_results:
                        results.extend(file_results)
                except Exception as file_error:
                    print(f"Error processing file {file_name}: {file_error}")
                    continue
            print("reference number", reference_number)
            line_data = self.extract_line_data(file_content)
            for count, line in enumerate(self.pending_ids.estimate_line_ids, start=1):
                if count <= len(line_data):
                    line_info = line_data[count - 1]
                    line.labour_cost_by_shipping_line = line_info.get("labour_cost", 0)
                    line.total_by_shipping_line = line_info.get("shipping_cost", 0)
                    line.material_cost_by_shipping_line = line_info.get("material_cost", 0)
                matching_result = next(
                    (result for result in results if result and result['damage_count'] == str(count)),
                    None
                )
                if matching_result:
                    line_item_status = matching_result.get('line_item_status')
                    if line_item_status == '5':
                        line.repair_status = 'approved'
                    elif line_item_status == '6':
                        line.repair_status = 'partially_approved'
                    else:
                        line.repair_status = 'rejected'
            # update overall status
            get_line_status = self.pending_ids.estimate_line_ids.mapped('repair_status')
            if all(status == 'approved' for status in get_line_status):
                self.repair_status = 'approved'
            elif all(status == 'rejected' for status in get_line_status):
                self.repair_status = 'rejected'
            else:
                self.repair_status = 'partially_approved'
            sftp.close()
            return True
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False

    @api.model
    def response_westim(self):
        """
        generate westim response based on mentioned FTP location and update the data in this system.
        :return:
        """
        get_waiting_approval_recs = self.search([('repair_status','=','awaiting_approval')])
        for rec in get_waiting_approval_recs:
            rec.update_estimate_lines_records()
        return False
