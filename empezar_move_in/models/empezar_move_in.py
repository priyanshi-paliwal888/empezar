# -*- coding: utf-8 -*-
import datetime
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.addons.empezar_base.models.res_users import ResUsers
import pytz


class MoveIn(models.Model):

    _name = "move.in"
    _description = "Move In"
    _order = 'id DESC'
    _rec_name = 'display_name'

    @staticmethod
    def get_years():
        """
        Generate a list of tuples containing years from 1950 to 3999.

        Returns:
            list: A list of tuples where each tuple contains a year
             as a string in the format (year, year).

        Example:
            >> get_years
            [('1950', '1950'), ('1951', '1951'), ..., ('3999', '3999')]
        """
        year_list = []
        for i in range(1950, 4000):
            year_list.append((str(i), str(i)))
        return year_list

    @api.model
    def get_allowed_companies_domain(self):
        """
        Return domain for location in move-in.
        :return:
        """
        get_main_company = self.env['res.company'].search([('active', '=', True),
                                                           ('parent_id', '=', False)]).ids
        allowed_companies = self.env.user.company_ids.ids
        allow_ids = list(set(allowed_companies) - set(get_main_company))
        return [('id', 'in', allow_ids)]

    shipping_line_logo = fields.Binary(string="Shipping Line Logo", related="shipping_line_id.logo")
    location_id = fields.Many2one('res.company',
                                  domain=lambda self: self.get_allowed_companies_domain(),
                                  default=lambda self: self.env.user.company_id)
    move_in_date_time = fields.Datetime(string="Move In Date Range", default=fields.Datetime.now)
    active = fields.Boolean(string="Status", default=True)
    rec_status = fields.Selection(
        [
            ("active", "Active"),
            ("disable", "Disable"),
        ],
        default="active",
        string="Status", compute="_compute_move_in_check_active_records")
    container_status = fields.Char(string="Container Status", compute="set_container_status")
    movement_type = fields.Selection([
        ('import_destuffing', 'Import Destuffing'),
        ('repo', 'Repo'),
        ('factory_return', 'Factory Return')
    ])
    do_no_id = fields.Many2one('delivery.order', string="DO/Booking No.")
    do_date = fields.Date(string="DO Date", related="do_no_id.delivery_date")
    do_validity_datetime = fields.Datetime("Validity Datetime",
                                           related='do_no_id.validity_datetime')
    validity_status = fields.Char(compute='_compute_validity_status', string='Validity Status', readonly=True)
    do_balance_container = fields.Char(string="Balance Container",
                                       compute="_get_do_balance_container")
    booking_no_id = fields.Many2one('vessel.booking', string="DO/Booking No.")
    booking_date = fields.Date(string="Booking Date", related="booking_no_id.booking_date")
    booking_validity_datetime = fields.Datetime(string="Validity Datetime",
                                                related="booking_no_id.validity_datetime")
    booking_balance_container = fields.Char(string="Balance Container", compute="_compute_balance_containers", store=True)
    remarks = fields.Char(string="Remarks", size=512)
    transporter_allotment_id = fields.Many2one('res.partner', string="Transporter Allotment",
                                        domain="[('parties_type_ids.name', '=', 'Transporter')]")
    transporter_full_filled_id = fields.Many2one('res.partner', string="Transporter FullFilled",
                                        domain="[('parties_type_ids.name', '=', 'Transporter')]")
    parties_importer = fields.Many2one('res.partner', string="Importer",
                                       domain="[('parties_type_ids.name', '=', 'Importer')]")
    parties_cha = fields.Many2one('res.partner', string="CHA",
                                  domain="[('parties_type_ids.name', '=', 'CHA')]")
    billed_to_party = fields.Many2one('res.partner', string="Billed to party",
                                      domain="[('is_cms_parties', '=', True),"
                                             "('is_this_billed_to_party', '=', 'yes')]")
    import_destuffing_from = fields.Selection(
        [
            ('factory', 'Factory'),
            ('CFS/ICD', 'CFS/ICD')
        ], string="Import Destuffing From")
    repo_from = fields.Selection(
        [
            ('port_terminal', 'Port/Terminal'),
            ('CFS/ICD', 'CFS/ICD'),
            ('empty_yard', 'Empty Yard')
        ], string="Repo From")
    from_factory = fields.Char(string="Factory", size=128)
    from_cfs_icd = fields.Many2one(
        "container.facilities", string="CFS/ICD",
        domain="[('facility_type', '=', 'cfs')]")
    from_port = fields.Many2one('master.port.data', string="Port")
    from_terminal = fields.Many2one(
        "container.facilities", string="Terminal",
        domain="[('port', '=', from_port),('facility_type', '=', 'terminal')]")
    from_empty_yard = fields.Many2one(
        "container.facilities", string="Empty yard",
        domain="[('facility_type', '=', 'empty_yard')]")
    display_create_info = fields.Char(compute="_get_create_record_info")
    display_modified_info = fields.Char(compute="_get_modify_record_info")
    display_sources = fields.Char(string="Source", readonly=True, default="Web")
    grade = fields.Selection([
        ('a', 'A'),
        ('b', 'B'),
        ('c', 'C'),
    ], string="Grade", required=True)
    damage_condition = fields.Many2one('damage.condition', string="Damage",
                                       required=True)
    shipping_line_id = fields.Many2one('res.partner', required=True)
    is_seal_return = fields.Selection([
        ('yes', 'Yes Return'),
        ('no', 'No'),
    ])
    # Computed domain field
    shipping_line_domain = fields.Many2many('res.partner', compute='_compute_shipping_line_domain')
    type_size_id = fields.Many2one('container.type.data', string="Type/Size", required=True)
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
        ])
    year = fields.Selection(get_years())
    gross_wt = fields.Char(string="Gross Wt. (KG)", size=12)
    tare_wt = fields.Char(string="Tare Wt. (KG)", size=12)
    seal_no_1 = fields.Char(string="Seal No.1", size=10)
    seal_no_2 = fields.Char(string="Seal No.2", size=10)
    laden_status = fields.Selection([
        ('laden', 'Laden'),
        ('empty', 'Empty')
    ])
    is_laden_status_readonly = fields.Boolean(string="Is laden status readonly",
                                              compute="make_laden_status_readonly")
    mode = fields.Selection([
        ('truck', 'Truck'),
        ('rail', 'Rail'),
    ], required=True)
    is_mode_readonly = fields.Boolean(string="Is Mode Readonly",
                                      compute="_compute_make_mode_readonly")
    truck_no = fields.Char(string="Truck No.", size=10)
    driver_name = fields.Char(string="Driver Name", size=56)
    driver_mobile_no = fields.Char(string="Driver Mobile No.", size=10)
    driver_licence_no = fields.Char(string="Driver Licence No.", size=36)
    rake_no = fields.Char(string="Rake No.", size=36)
    wagon_no = fields.Char(string="Wagon No.", size=36)
    stack = fields.Selection([
        ('lower_deck', 'L/D (Lower Deck)'),
        ('upper_deck', 'U/D (Upper Deck)')
    ])
    patch_count = fields.Integer(string="Patch Count")
    is_patch_count_visible = fields.Boolean(string="Is Patch Count Visible",
                                            compute="patch_count_visibility")
    field_visibility = fields.Json("Fields Visibility", compute='_compute_field_visibility_required')
    field_required = fields.Json("Fields Required", compute='_compute_field_visibility_required')
    gate_pass_visible = fields.Boolean(default=False, compute='_compute_gate_pass_visibility')
    gate_pass_no = fields.Char(copy=False, readonly=True, string="Gate Pass No.")

    # This field has a value only if container survey is completed.
    container_survey_id = fields.Integer(string="Container Survey Id")
    booking_number_url = fields.Html(compute='_compute_booking_number_url', string='Booking URL', store=False)
    delivery_order_url = fields.Html(compute='_compute_delivery_order_url', string='Delivery order URL', store=False)
    container = fields.Char("Container No.", copy=False, size=11, required=True)
    is_time_editable = fields.Boolean('Is Time Editable', default=True)
    is_edi_send = fields.Boolean(string="Is EDI sent ?", default=False)
    is_damage_edi_send = fields.Boolean(string="Is Damage EDI sent ?", default=False)
    edi_sent_on = fields.Datetime(string="In EDI Sent On")
    damage_edit_sent_on = fields.Date(string="Damage EDI Sent On")
    edi_in_attachment_id = fields.Many2one('ir.attachment', string='Related attachment')
    type_size_domain = fields.Char(string="Domain", compute='_compute_type_size_domain')


    def cancel_edit(self):
        for record in self:
            if record.move_in_date_time and self.env.context.get('is_edit_time') == 0:
                record.is_time_editable = False

    def edit_time(self):
        for record in self:
            if record.move_in_date_time and self.env.context.get('is_edit_time') == 1:
             record.is_time_editable = True

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

    @api.onchange('truck_no')
    def _onchange_truck_number(self):
        if self.truck_no:
            self.truck_no = self.truck_no.upper()

    @api.depends('booking_no_id')
    def _compute_balance_containers(self):
        """Computes and updates the balance and size types of containers associated with the
        booking.
        """
        for record in self:
            combined_str = ""
            for container in record.booking_no_id.container_details:
                container_size_type_code = container.container_size_type.company_size_type_code
                balance = container.balance
                combined_entry = f"{container_size_type_code} (*{balance})"
                if combined_str:
                    combined_str += " , "
                combined_str += combined_entry
            record.booking_balance_container = combined_str
    
    @api.depends('do_no_id')
    def _compute_delivery_order_url(self):
        for record in self:
            if record.do_no_id:
                delivery_order = record.do_no_id
                url = '/web#id=%s&model=%s' % (delivery_order.id, 'delivery.order')
                record.delivery_order_url = '<a href="%s">%s</a>' % (url, delivery_order.delivery_no)
            else:
                record.delivery_order_url = '#'

    @api.depends('booking_no_id')
    def _compute_booking_number_url(self):
        for record in self:
            if record.booking_no_id:
                booking_number = record.booking_no_id
                url = '/web#id=%s&model=%s' % (booking_number.id, 'vessel.booking')
                record.booking_number_url = '<a href="%s">%s</a>' % (url, booking_number.booking_no)
            else:
                record.booking_number_url = '#'

    @api.depends('do_validity_datetime', 'booking_validity_datetime')
    def _compute_validity_status(self):
        today = fields.Date.today()
        for record in self:
            if record.do_validity_datetime or record.booking_validity_datetime:
                validity_date = fields.Date.from_string(record.do_validity_datetime) or fields.Date.from_string(record.booking_validity_datetime)
                if validity_date < today:
                    record.validity_status = 'Expired'
                else:
                    record.validity_status = ''
            else:
                record.validity_status = ''

    @api.depends('location_id')
    def _compute_field_visibility_required(self):
        for record in self:
            if record.location_id:
                settings = record.location_id.movement_move_in_settings_ids
                visible_fields = {setting.field_name.name: setting.show_on_screen for setting in settings}
                record.field_visibility = visible_fields
                required_fields = {setting.field_name.name: setting.mandatory == 'yes' for setting in settings}
                record.field_required = required_fields
            else:
                record.field_visibility = {}
                record.field_required = {}

    @api.model
    def default_get(self, fields_list):
        """Overrides default_get to set `mode` and `laden_status` based on `location_id`.
        """
        res = super().default_get(fields_list)
        if res.get('location_id'):
            location_obj = self.env['res.company'].sudo().search(
                [('id', '=', res.get('location_id'))], limit=1)
            if location_obj:
                location_modes = location_obj.mode_ids.mapped('name')
                location_laden_status = location_obj.laden_status_ids.mapped('name')
                if len(location_modes) == 1:
                    if 'Rail' in location_modes:
                        res['mode'] = 'rail'
                    else:
                        res['mode'] = 'truck'
                if len(location_laden_status) == 1:
                    if 'Laden' in location_laden_status:
                        res['laden_status'] = 'laden'
                    else:
                        res['laden_status'] = 'empty'
        return res

    def set_container_status(self):
        """
        Set container status based on inventory.
        """
        # Get the selection dictionary for the 'status' field
        status_selection = dict(self.env['container.inventory']._fields['status'].selection)

        for rec in self:
            rec.container_status = ''
            # Search for the related container.inventory record
            inventory_record = self.env['container.inventory'].with_context(active_test=False).search([
                ('move_in_id', '=', rec.id),
            ], limit=1)

            # If a record is found, set the container_status to the display value of 'status'
            if inventory_record:
                rec.container_status = status_selection.get(inventory_record.status, '')

    @api.depends('location_id')
    def _compute_make_mode_readonly(self):
        """Sets `is_mode_readonly` based on the `location_id` mode and updates `mode` accordingly."""
        for record in self:
            location_mode = record.location_id.mode_ids.mapped('name') if record.location_id else []

            if 'Rail' in location_mode and 'Truck' in location_mode:
                record.is_mode_readonly = False
            elif 'Rail' in location_mode:
                record.mode = 'rail'
                record.is_mode_readonly = True
            elif 'Truck' in location_mode:
                record.mode = 'truck'
                record.is_mode_readonly = True
            else:
                record.is_mode_readonly = False

    @api.depends('container','type_size_id')
    def _compute_display_name(self):
        """Computes and sets the display name based on the container's name and company size type code."""
        for record in self:
            if record.container:
                if record.type_size_id.company_size_type_code:
                    record.display_name = f'{record.container}({record.type_size_id.company_size_type_code})'
                else:
                    record.display_name = record.container
            else:
                record.display_name = False

    @api.depends('location_id')
    def _compute_shipping_line_domain(self):
        """
        Compute shipping line domain based on location.
        """
        for record in self:
            if record.location_id:
                # Fetch the shipping lines based on the location_id
                shipping_lines = record.location_id.shipping_line_mapping_ids.mapped('shipping_line_id')
                record.shipping_line_domain = [(6, 0, shipping_lines.ids)]
            else:
                record.shipping_line_domain = []

    @api.constrains(
        'transporter_allotment_id',
        'transporter_full_filled_id',
        'parties_importer',
        'parties_cha',
        'billed_to_party',
        'location_id'
    )
    def check_record_is_active_or_not(self):
        """
        Check the mentioned record is active or not.
        """
        self.ensure_one()

        # Dictionary to map field names to their respective display attributes and error messages
        field_mapping = {
            'transporter_allotment_id': ('party_name', _('Please choose an active party.')),
            'transporter_full_filled_id': ('party_name', _('Please choose an active party.')),
            'parties_importer': ('party_name', _('Please choose an active party.')),
            'parties_cha': ('party_name', _('Please choose an active party.')),
            'billed_to_party': ('party_name', _('Please choose an active party.')),
            'location_id': ('name', _('Please choose an active location.')),
        }
        for field_name, (display_field, error_msg) in field_mapping.items():
            field = getattr(self, field_name)
            if field and not field.active:
                raise ValidationError(_('%s is not active. %s') % (getattr(field, display_field), error_msg))

    @api.depends('type_size_id', 'shipping_line_id')
    def patch_count_visibility(self):
        """
        Patch count visibility based on the mapped type/size.
        """
        for rec in self:
            rec.is_patch_count_visible = False

            if rec.type_size_id:
                if rec.type_size_id.is_refer == 'no':
                    continue  # Skip further processing for this record

                if rec.type_size_id.is_refer == 'yes' and rec.location_id and rec.shipping_line_id:
                    mapped_shipping_lines = rec.location_id.shipping_line_mapping_ids.filtered(
                        lambda a: a.shipping_line_id == rec.shipping_line_id and a.refer_container == 'yes'
                    )
                    # If any mapped shipping lines meet the criteria, set visibility to True
                    if mapped_shipping_lines and rec.field_visibility and rec.field_visibility.get('patch_count'):
                        rec.is_patch_count_visible = True
                        continue  # No need to check further lines if already True

    @api.onchange('patch_count')
    @api.constrains('patch_count')
    def onchange_patch_count(self):
        """
        Patch count validations.
        """
        for record in self:
            if not (0 <= record.patch_count <= 9999):
                raise ValidationError("Maximum 4 digits allowed or positive values.")

    @api.depends('location_id')
    def make_laden_status_readonly(self):
        """
        Laden status field assignment and visibility
        based on conditions.
        """
        if self.location_id:
            location_laden_status = self.location_id.laden_status_ids.mapped('name')
            if len(location_laden_status) > 1:
                self.is_laden_status_readonly = False
            else:
                if 'Laden' in location_laden_status:
                    self.laden_status = 'laden'
                else:
                    self.laden_status = 'empty'
                self.is_laden_status_readonly = True
        else:
            self.is_laden_status_readonly = False

    def _compute_move_in_check_active_records(self):
        """Update record status based on the 'active' field.
           Sets the 'rec_status' field to 'active' if 'active' is True,
           otherwise sets it to 'disable'.
        """
        for rec in self:
            if rec.active:
                rec.rec_status = "active"
            else:
                rec.rec_status = "disable"

    def check_digit_validation_for_container(self):
        # Define character to number mapping
        char_to_num_dict = {
            'A': 10, 'B': 12, 'C': 13, 'D': 14, 'E': 15, 'F': 16, 'G': 17, 'H': 18, 'I': 19,
            'J': 20, 'K': 21, 'L': 23, 'M': 24, 'N': 25, 'O': 26, 'P': 27, 'Q': 28, 'R': 29,
            'S': 30, 'T': 31, 'U': 32, 'V': 34, 'W': 35, 'X': 36, 'Y': 37, 'Z': 38
            }
        input_data = str(self.container).upper()
        sliced_input_data = input_data[:10]
        total_sum = sum(
            (char_to_num_dict.get(char) if char_to_num_dict.get(char) else int(char)) * (2 ** index)
            for index, char in enumerate(sliced_input_data)
        )
        rounded_division_result = (int(total_sum/11)) * 11
        remainder = total_sum - rounded_division_result
        new_digit = remainder % 10
        if new_digit != eval(self.container[-1]):
            raise ValidationError(_("Container Number is invalid."))

    @api.onchange('driver_mobile_no')
    @api.constrains('driver_mobile_no')
    def check_drive_mobile_no_validations(self):
        """
        Driver mobile number validations.
        """
        if self.mode == 'truck':
            if self.driver_mobile_no and len(self.driver_mobile_no) != 10:
                raise ValidationError(_('Driver mobile no. should be 10 digits only.'))
            if self.driver_mobile_no and not self.driver_mobile_no.isdigit():
                raise ValidationError(_('Only numeric values are allowed'))

    @api.depends('do_no_id')
    def _get_do_balance_container(self):
        """
        Computes and updates the balance and size types of containers associated with the
        delivery order.
        """
        for record in self:
            combined_str = ""
            for container in record.do_no_id.container_details:
                container_size_type_code = container.container_size_type.company_size_type_code
                balance = container.balance_container
                combined_entry = f"{container_size_type_code} (* {balance})"
                if combined_str:
                    combined_str += " , "
                combined_str += combined_entry
            record.do_balance_container = combined_str

    @api.onchange('location_id')
    def on_change_location_id(self):
        """
        Empty whole records while location is changed.
        """
        if self._context.get('is_location_change'):
            get_fields = self.fields_get()
            # List of fields to exclude from resetting if needed
            exclude_fields = ['id', 'create_date', 'write_date', 'create_uid',
                          'write_uid', 'location_id', 'mode','is_time_editable']

            for field_name, field_info in get_fields.items():
                if field_name not in exclude_fields:
                    # Check if the field is writable
                    if field_info.get('store', True):
                        setattr(self, field_name, False)
        if self.location_id:
            # Fetch the shipping lines based on the location_id
            shipping_lines = self.location_id.shipping_line_mapping_ids.mapped('shipping_line_id')

            if len(shipping_lines) == 1:
                # If there's only one shipping line, set it automatically
                self.shipping_line_id = shipping_lines[0]
            else:
                # If there are multiple shipping lines, clear the shipping line field or show options
                self.shipping_line_id = False
        else:
            self.shipping_line_id = False

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

    @api.onchange('move_in_date_time')
    @api.constrains('move_in_date_time')
    def _check_move_in_date_time(self):
        """
        Move in time field validations.
        """
        for record in self:
            if record.move_in_date_time and record.move_in_date_time > datetime.datetime.now():
                raise ValidationError(_("Move In Date/Time cannot be in the future."))

    @api.constrains('do_no_id')
    def _check_delivery_order_id(self):
        """Validates that the delivery order has a non-zero balance of containers.
        """
        for record in self:
            if record.do_no_id and not record.do_no_id.active:
                raise ValidationError(_('%s is not active. Please choose active Do.')
                                      % record.do_no_id.delivery_no)
            if record.do_no_id and record.do_no_id.balance_containers == 0 and record.movement_type == 'import_destuffing':
                raise ValidationError(_("There is no balance quantity in this "
                                        "DO/Booking. To update this go to record. "
                                        "Alternatively Choose another record"))


    @api.onchange('type_size_id')
    def check_container_type_size(self):
        for record in self:
            if record.do_no_id:
                if record.type_size_id.name not in record.do_no_id.container_details.mapped('container_size_type.name'):
                    raise ValidationError(
                        _("This container size/type is not available for the above selected delivery order."))
            if record.booking_no_id:
                if record.type_size_id.name not in record.booking_no_id.container_details.mapped('container_size_type.name'):
                    raise ValidationError(_("This container size/type is not available for the above selected vessel booking number."))

    @api.constrains('booking_no_id')
    @api.onchange('type_size_id')
    def _check_booking_order_id(self):
        """Validates that the delivery order has a non-zero balance of containers.
        """
        for record in self:
            if record.booking_no_id and not record.booking_no_id.active:
                raise ValidationError(_('%s is not active. Please choose active vessel booking.')
                                      % record.booking_no_id.booking_no)
            if record.booking_no_id and record.booking_no_id.balance_containers == 0:
                raise ValidationError(_("There is no balance quantity in this "
                                        "DO/Booking. To update this go to record. "
                                      "Alternatively Choose another record"))

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
                # Check if the value is exactly 12 digits
                if  not weight_value.isdigit():
                    raise ValidationError(_('The {} must be exactly 12 digits.').format(
                        self._fields[weight_field].string))

                weight_value_int = int(weight_value)

                if weight_value_int < 0:
                    raise ValidationError(_('Negative weight is not allowed for {}.').format(
                        self._fields[weight_field].string))

        if self.gross_wt and self.tare_wt and int(self.gross_wt) < int(self.tare_wt):
            raise ValidationError(_('Tare weight cannot be greater than gross weight'))

    @api.onchange('mode')
    @api.constrains('mode')
    def changes_in_mode(self):
        """
        When mode is change then other selection
        field value will be empty.
        """
        self.ensure_one()
        if self.mode:
            if self.mode == 'truck':
                self.rake_no = False
                self.wagon_no = False
                self.stack = False
            else:
                self.truck_no = False
                self.driver_name = False
                self.driver_mobile_no = ''
                self.driver_licence_no = False
                self.transporter_allotment_id = False
                self.transporter_full_filled_id = False

    def gate_pass(self):
        """
        Pass
        :return:
        """
        for record in self:
            # Check if Gate Pass Number is already set
            if not record.gate_pass_no:
                # Generate the Gate Pass number
                prefix = "GPMI2324"
                location_code = record.location_id.location_code
                sequence = self.env['ir.sequence'].next_by_code('move.in') or _("New")
                gate_pass_number = f"{prefix}{location_code}{sequence}"
                record.write({'gate_pass_no': gate_pass_number})

        return self.env.ref('empezar_move_in.move_in_report_action').report_action(self)

    def _get_report_file_name(self):
        for record in self:
            get_company = self.env['res.company'].search([('parent_id', '=', False), ('active', '=', True)], limit=1)
            company_format = get_company.date_format
            local_tz = pytz.timezone('Asia/Kolkata')
            local_dt = pytz.utc.localize(record.move_in_date_time).astimezone(local_tz)
            date_formats = {
                'DD/MM/YYYY': '%d/%m/%Y',
                'YYYY/MM/DD': '%Y/%m/%d',
                'MM/DD/YYYY': '%m/%d/%Y'
            }
            move_in_date = local_dt.strftime(date_formats.get(company_format, '%d/%m/%Y'))
            move_in_time =local_dt.strftime('%I:%M %p')
            formatted_time = move_in_time.replace('AM', '_AM').replace('PM', '_PM')
            file_name = f"GATEPASS_{record.container}_{move_in_date}_{formatted_time}"
            return file_name

    def view_edi(self):
        for record in self:
            # Fetch the edi.logs record where move_in_ids contains the current move.in record and location_id matches
            edi_log = self.env['edi.logs'].search([
                ('move_in_ids', 'in', record.ids),
                ('location_id', '=', record.location_id.id),
                ('shipping_line_id', '=', record.shipping_line_id.id),
            ], limit=1)  # Assuming you want to open the first matching record

            if edi_log:
                # Return the action to open the edi.logs form view
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'View EDI',
                    'res_model': 'edi.logs',
                    'res_id': edi_log.id,
                    'view_mode': 'form',
                    'domain': [('move_in_ids', '=', self.id)],
                    'views': [(self.env.ref('empezar_edi.edi_logs_tree_view').id, 'tree')],
                    'target': 'new',  # Open the form in a pop-up window
                }
            else:
                # Handle the case where no matching edi.logs record is found
                pass

    def download_gate_pass(self):
        """
        Download gate pass functionality.
        """
        for record in self:
            if not record.gate_pass_no:
                raise ValidationError("The gate pass has not been generated. Please generate the gate pass.")
            else:
                return self.env.ref('empezar_move_in.move_in_report_action').report_action(self)

    def download_in_edi(self):
        """Pass
        :return:
        """
        if self.edi_in_attachment_id:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s?download=true' % self.edi_in_attachment_id.id,
                'target': 'self',
            }
        else:
            raise ValidationError('No attachment found to download.')

    def download_repair_edi(self):
        """Pass
        :return:
        """
        pass

    @api.depends('location_id')
    def _compute_gate_pass_visibility(self):
        """
        Gate-pass visibility functionality.
        """
        for record in self:
            if record.location_id:
                # Fetch the shipping lines based on the location_id
                shipping_lines = record.location_id.shipping_line_mapping_ids.mapped('shipping_line_id')
                if shipping_lines and record.shipping_line_id in shipping_lines:
                    val = record.location_id.shipping_line_mapping_ids.filtered(lambda act: act.shipping_line_id == record.shipping_line_id)
                    if 'Move In' in val.gate_pass_ids.mapped('name'):
                        record.gate_pass_visible = True
                    else:
                        record.gate_pass_visible = False
                else:
                    record.gate_pass_visible = False

    @api.constrains('seal_no_1', 'seal_no_2')
    def change_seal_status(self):
        """
        Update the seal status in the seal master
        based on the conditions while done move in.
        """
        if self.seal_no_1 and self.movement_type == 'factory_return' and self.is_seal_return == 'yes'\
                and self.location_id:
            seal_numbers = [self.seal_no_1]
            if self.seal_no_2:
                seal_numbers.append(self.seal_no_2)

            seals = self.env['seal.management'].search([('seal_number', 'in', seal_numbers),
                                                        ('location', '=', self.location_id.id)])
            for seal in seals:
                seal.rec_status = 'available'
                seal.container_number = '-'

    @api.onchange('is_seal_return')
    def onchange_is_seal_return(self):
        """
        Empty seal-no-1 field based on the condition.
        """
        if self.movement_type == 'factory_return' and self.is_seal_return == 'no':
            self.seal_no_1 = False

    @api.depends('shipping_line_id', 'location_id')
    def _compute_type_size_domain(self):
        for record in self:
            if record.shipping_line_id and record.location_id:
                # Fetch the `refer_container` value from the shipping line mapping for this location and shipping line
                mapping = self.env['location.shipping.line.mapping'].search([
                    ('shipping_line_id', '=', record.shipping_line_id.id),
                    ('company_id', '=', record.location_id.id)
                ], limit=1)
                if mapping:
                    if mapping.refer_container == 'yes':
                        record.type_size_domain = [('is_refer', '=', 'yes')]
                    elif mapping.refer_container == 'no':
                        record.type_size_domain = [('is_refer', '=', 'no')]
                else:
                    record.type_size_domain = []
            else:
                record.type_size_domain = []

    def disable_move_in_validations(self):
        if self.container:
            user_time = fields.Datetime.context_timestamp(self, self.move_in_date_time)
            move_in_date = user_time.date()
            hour = user_time.hour
            minute = user_time.minute
            check_inventory = self.env['container.inventory'].search([('name', '=', self.container),
                                                                      ('location_id','=',self.location_id.id)])
            get_move_out_records = self.env['container.inventory'].search([('active','=',False),
                                                                           ('name','=',self.container),
                                                                           ('location_id','=',self.location_id.id),
                                                                           ('move_out_date','>=',move_in_date),
                                                                           ('out_hour','>=',hour),
                                                                           ('out_minutes','>=',minute)])
            if not check_inventory or get_move_out_records:
                raise ValidationError(
                    _('The Move In record cannot be disabled as a Move Out entry is found for this container.'))
        else:
            raise ValidationError(
                _('No container found.'))


    def update_move_in_balance_containers(self):
        """
        Updates the `balance_containers` value in the associated delivery order
        or booking based on the type size match.
        """
        if self.do_no_id:
            delivery_order = self.do_no_id
            # Find the matching container type in the delivery order
            matching_container = delivery_order.container_details.filtered(
                lambda c: c.container_size_type.name == self.type_size_id.name
            )
            if matching_container:
                matching_container.balance_container += 1
            else:
                raise ValidationError(
                    _("No matching container type found in the delivery order.")
                )
        elif self.booking_no_id:
            booking_order = self.booking_no_id
            # Find the matching container type in the booking order
            matching_container = booking_order.container_details.filtered(
                lambda c: c.container_size_type.name == self.type_size_id.name
            )
            if matching_container:
                matching_container.balance += 1
            else:
                raise ValidationError(
                    _("No matching container type found in the booking order.")
                )
        else:
            raise ValidationError(
                _("No associated delivery or booking found for the record.")
            )

    def disable_move_in_linked_invoice_validations(self):
        """
        Disable linked invoice validations.
        """
        for record in self:
            move_in_invoice_records = self.env['move.in.out.invoice'].search([
                ('move_in_id', '=', record.id)])
            if move_in_invoice_records:
                for invoice in move_in_invoice_records:
                    if invoice.invoice_status == 'active':
                        raise ValidationError(_("The Move In Record cannot be disabled as active invoices are linked to this Move In Record."))


    @api.model
    def write(self, vals):
        try:
            if 'active' in vals and vals['active'] == True:
                raise ValidationError(_("You cannot unarchive a record. Please create a new record instead."))
            if 'active' in vals and vals['active'] == False:
                self.disable_move_in_linked_invoice_validations()
                self.disable_move_in_validations()
                self.env['container.inventory'].search([('move_in_id', '=', self.id),('location_id','=',self.location_id.id)], limit=1).unlink()
                self.update_move_in_balance_containers()
        except Exception as e:
            raise ValidationError(_(e))
        return super(MoveIn, self).write(vals)
