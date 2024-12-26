from datetime import datetime
import pytz
from pytz import timezone
from odoo.exceptions import ValidationError, UserError
from odoo import fields, models, api, exceptions, _
from odoo.addons.empezar_base.models.res_users import ResUsers


class MoveOut(models.Model):
    _name = "move.out"
    _description = "Move Out"
    _order = 'id DESC'
    _rec_name = 'display_name'

    @api.model
    def _get_allowed_companies_domain(self):
        """
        Return domain for location in move-in.
        :return:
        """
        get_main_company = self.env['res.company'].search([('active', '=', True),
                                                           ('parent_id', '=', False)]).ids
        allowed_companies = self.env.user.company_ids.ids
        allow_ids = list(set(allowed_companies) - set(get_main_company))
        return [('id', 'in', allow_ids)]



    shipping_line_logo = fields.Binary(
        string="Carrier", related="shipping_line_id.logo")
    shipping_line_id = fields.Many2one(
        "res.partner",
        string="Shipping Line",
        domain="[('is_shipping_line', '=', True),('applied_for_interchange','=', 'yes')]",
        required=True
    )
    shipping_line_domain = fields.Char(
        string="Shipping Line Domain",
        compute="_compute_shipping_line_domain"
    )
    remark = fields.Char(string="Remarks", size=512)
    rec_status = fields.Selection(
        [
            ("active", "Active"),
            ("disable", "Disable"),
        ],
        default="active",
        string="Status", compute="_compute_move_out_check_active_records")
    active = fields.Boolean(string="Active", default=True)
    location_id = fields.Many2one('res.company',
                                  domain=lambda self: self._get_allowed_companies_domain(),
                                  string="Location", required=True,
                                  default=lambda self: self.env.user.company_id)
    container_id = fields.Many2one('container.master', related='inventory_id.container_master_id')
    inventory_id = fields.Many2one('container.inventory', string="Inventory",
                                   domain="[('location_id', '=', location_id)]", copy=False)
    move_out_date_time = fields.Datetime(string="Move Out Date Range", required=True,
                                         default=fields.Datetime.now)
    container_status = fields.Selection(related='inventory_id.status',
                                        string="Container Status")
    damage_condition_id = fields.Many2one(related='inventory_id.damage_condition', string="Damage")
    movement_type = fields.Selection(
        [
            ('export_stuffing', 'Export Stuffing'),
            ('repo', 'Repo')
        ], string="Movement Type", required=True)
    export_stuffing_to = fields.Selection(
        [
            ('factory', 'Factory'),
            ('CFS/ICD', 'CFS/ICD')
        ], string="Export Stuffing To")
    repo_to = fields.Selection(
        [
            ('port_terminal', 'Port/Terminal'),
            ('CFS/ICD', 'CFS/ICD'),
            ('empty_yard', 'Empty Yard')
        ], string="Repo")
    to_factory = fields.Char(string="Factory", size=128)
    to_cfs_icd_id = fields.Many2one(
        "container.facilities", string="CFS/ICD",
        domain="[('facility_type', '=', 'cfs')]")
    to_cfs_icd_repo_id = fields.Many2one(
        "container.facilities", string="CFS/ICD",
        domain="[('facility_type', '=', 'cfs')]")
    to_port_id = fields.Many2one('master.port.data', string="Port")
    to_terminal_id = fields.Many2one(
        "container.facilities", string="Terminal",
        domain="[('facility_type', '=', 'terminal'),('port', '=', to_port_id)]")
    to_empty_yard_id = fields.Many2one(
        "container.facilities", string="Empty yard",
        domain="[('facility_type', '=', 'empty_yard')]")
    display_create_info = fields.Char(compute="_compute_get_create_record_info")
    display_modified_info = fields.Char(compute="_compute_get_modify_record_info")
    display_sources = fields.Char(string="Sources", readonly=True, default="User Entry")
    is_shipping_line_interchange = fields.Selection(
        [
            ('yes', 'YES'),
            ('no', 'NO'),
        ], string="Is Shipping Line Interchange", default='no')
    transporter_allocated_id = fields.Many2one(
        "res.partner", string="Transporter(Allocated)",
        domain="[('parties_type_ids.name', '=', 'Transporter')]")
    transporter_fulfilled_id = fields.Many2one(
        "res.partner", string="Transporter (Fulfilled)",
        domain="[('parties_type_ids.name', '=', 'Transporter')]")
    exporter_name_id = fields.Many2one(
        "res.partner", string="Exporter Move out",
        domain="[('parties_type_ids.name', '=', 'Exporter')]")
    cha_name_id = fields.Many2one(
        "res.partner", string="CHA",
        domain="[('parties_type_ids.name', '=', 'CHA')]")
    delivery_order_id = fields.Many2one("delivery.order", string="DO/Booking No.",
                                        domain="[('location', 'in', location_id)]")
    booking_no_id = fields.Many2one('vessel.booking', string="DO/Booking No.",
                                    domain="[('location', 'in', location_id)]")
    delivery_order_date = fields.Date("DO Date", related='delivery_order_id.delivery_date')
    validity_status = fields.Char(compute='_compute_validity_status', string='Validity Status', readonly=True)
    validity_datetime = fields.Datetime("Validity Datetime",
                                        related='delivery_order_id.validity_datetime')
    exporter_delivery_order_id = fields.Many2one("res.partner", "Exporter",
                                                 related='delivery_order_id.exporter_name')
    booking_order_date = fields.Date("Booking Date",
                                     related='booking_no_id.booking_date')
    booking_validity_datetime = fields.Datetime("Validity Datetime",
                                                related='booking_no_id.validity_datetime')
    port_discharge_booking_id = fields.Many2one("master.port.data", "Port Discharge",
                                                related='booking_no_id.port_discharge')
    type_size_id = fields.Many2one('container.type.data', string="Type/Size",related='inventory_id.container_master_id.type_size')
    company_size_type = fields.Char("Type/Size",related = 'inventory_id.container_master_id.type_size.company_size_type_code')
    production_month_year = fields.Char("Production Month/Year", related = 'inventory_id.container_master_id.production_month_year')
    gross_wt = fields.Integer(string="Gross Wt. (KG)", related='inventory_id.container_master_id.gross_wt', size=12)
    tare_wt = fields.Integer(string="Tare Wt. (KG)", related='inventory_id.container_master_id.tare_wt', size=12)
    move_in_date_time = fields.Datetime(string="Move In Date Time")
    created_by_id = fields.Many2one('res.users', string='Created By')
    seal_no_1 = fields.Many2one('seal.management', string='Seal Number 1',
                                domain="[('location', '=', location_id),"
                                       "('rec_status', '=', 'available'),"
                                       "('shipping_line_id','=',shipping_line_id)]")
    seal_no_2 = fields.Many2one('seal.management', string='Seal Number 2',
                                domain="[('location', '=', location_id),"
                                       "('rec_status', '=', 'available'),"
                                       "('shipping_line_id','=',shipping_line_id)]")
    grade = fields.Selection([
        ('a', 'A'),
        ('b', 'B'),
        ('c', 'C'),
    ],  string="Grade", related="inventory_id.grade", readonly=False, required=True)
    truck_number = fields.Char(string="Truck Number", size=10)
    driver_name = fields.Char("Driver Name", size=56)
    driver_mobile_number = fields.Char("Driver Mobile Number", size=10)
    driver_licence_no = fields.Char("Driver Licence Number", size=36)
    driver_photo = fields.Binary()
    mode = fields.Selection([("truck", "Truck"), ("rail", "Rail")], string="Mode", required=True)
    is_mode_readonly = fields.Boolean(string="Is Mode Readonly", compute="_compute_make_mode_readonly")
    rake_number = fields.Char("Rake Number", size=36)
    wagon_number = fields.Char("Wagon Number", size=36)
    stack = fields.Selection([
        ('L/D', "Lower Deck"),
        ('U/D', "Upper Deck")
    ])
    laden_status = fields.Selection([
        ('empty', "Empty"),
        ('laden', "Laden")
    ])
    is_laden_status_readonly = fields.Boolean(string="Is laden status readonly",
                                              compute="_compute_make_laden_status_readonly")
    temperature = fields.Integer("Temperature")
    is_temperature = fields.Boolean("Is temperature",
                                    compute='_compute_check_temperature_validations')
    humidity = fields.Integer("Humidity")
    is_humidity = fields.Boolean("Is Humidity", compute='_compute_check_humidity_validations')
    vent = fields.Integer("Vent")
    is_vent = fields.Boolean("Is Vent", compute='_compute_check_vent_validations')
    vent_seal_no = fields.Char("Vent Seal Number", size=128)
    is_vent_seal_number = fields.Boolean("Is Vent Seal Numbers",
                                         compute='_compute_check_vent_seal_no_validations')
    booking_balance_and_type_sizes = fields.Char(string="Booking Balance",
                                                 compute='_compute_balance_containers', store=True)
    delivery_order_balance_and_type_sizes = fields.Char(string="Delivery order Balance",
                                                        compute='_compute_delivery_order_balance_containers',
                                                        store=True)
    field_visibility = fields.Json("Fields Visibility", compute='_compute_field_visibility_required')
    field_required = fields.Json("Fields Required", compute='_compute_field_visibility_required')
    gate_pass_visible = fields.Boolean(default=False, compute='_compute_gate_pass_visibility')
    gate_pass_no = fields.Char(copy=False, readonly=True, string="Gate Pass No.")
    billed_to_party = fields.Many2one('res.partner', string="Billed to party",
                                      domain="[('is_cms_parties', '=', True),"
                                             "('is_this_billed_to_party', '=', 'yes')]")
    release_container = fields.Selection([
        ('yes_release', "Yes Release"),
        ('cancel', "Cancel")
    ])
    is_container_on_hold = fields.Boolean("Hold container", default=False)
    delivery_order_compute_domain = fields.Many2many('delivery.order', string="Delivery prder Domain",
                                                    compute="_compute_delivery_domain")
    vessel_booking_compute_domain = fields.Many2many('vessel.booking', string="Vessel Booking Domain",
                                                     compute="_compute_booking_domain")
    move_in_id = fields.Many2one("move.in", string="Move In")
    booking_number_url = fields.Html(compute='_compute_booking_number_url', string='Booking URL',
                                     store=False)
    delivery_order_url = fields.Html(compute='_compute_delivery_order_url',
                                     string='Delivery order URL', store=False)
    move_in_url = fields.Html(compute='_compute_move_in_url',
                                     string='Move In URL', store=False)
    original_shipping_line = fields.Char("Original Shipping line",compute='_compute_original_shipping_line')
    is_time_editable = fields.Boolean('Is Time Editable', default=True)
    is_shipping_line_visible = fields.Boolean(default=False)
    is_edi_send = fields.Boolean(string="Is EDI sent ?", default=False)
    edi_out_attachment_id = fields.Many2one('ir.attachment', string='Move Out EDI')
    is_repair_edi_send = fields.Boolean(string="Is Repair EDI sent ?", default=False)
    edi_sent_on = fields.Datetime(string="Out EDI Sent On")
    repair_edit_sent_on = fields.Date(string="Repair EDI Sent On")

    @api.onchange('is_shipping_line_interchange')
    def _compute_shipping_line_domain(self):
        for record in self:
            domain = [('is_shipping_line', '=', True), ('applied_for_interchange', '=', 'yes')]
            if record.is_shipping_line_interchange == 'yes':
                domain.append(('id', '!=', record.container_id.shipping_line_id.id))
            record.shipping_line_domain = str(domain)

    @api.onchange('inventory_id')
    def _reset_shipping_line_interchange(self):
        for record in self:
            record.is_shipping_line_interchange = 'no'

    @api.constrains('move_out_date_time')
    def _move_out_date_time(self):
        ist = pytz.timezone('Asia/Kolkata')
        for record in self:
            if record.inventory_id:
                if record.move_out_date_time:
                    move_out_date_time_ist = record.move_out_date_time.astimezone(ist)
                    move_out_date = move_out_date_time_ist.date()
                    current_hour = move_out_date_time_ist.hour
                    current_minute = move_out_date_time_ist.minute
                else:
                    move_out_date = None
                    current_hour = None
                    current_minute = None

                record.inventory_id.write({
                    'move_out_date': move_out_date,
                    'out_hour': str(current_hour),
                    'out_minutes': str(current_minute),
                })
                record.inventory_id.active = False

    @api.onchange('inventory_id', 'shipping_line_id')
    def onchange_container(self):
        for record in self:
            if record.shipping_line_id and record.original_shipping_line:
                if record.shipping_line_id.shipping_line_name != record.original_shipping_line:
                    record.is_shipping_line_visible = True
                else:
                    record.is_shipping_line_visible = False

    @api.onchange('is_shipping_line_interchange')
    def onchange_is_shipping_line_interchange(self):
        for record in self:
            if record.is_shipping_line_interchange == 'no':
                record.shipping_line_id = record.container_id.shipping_line_id
            if record.is_shipping_line_interchange == 'yes':
                record.shipping_line_id = False

    @api.constrains('is_shipping_line_interchange')
    def shipping_line_interchange(self):
        for record in self:
            if record.is_shipping_line_interchange == 'yes':
                container_id = self.env['container.master'].search([('name','=',record.container_id.name)])
                container_id.write({
                    'shipping_line_id':record.shipping_line_id.id
                })

    def cancel_edit(self):
        for record in self:
            if record.move_in_date_time and self.env.context.get('is_edit_time') == 0:
                record.is_time_editable = False

    def edit_time(self):
        for record in self:
            if record.move_in_date_time and self.env.context.get('is_edit_time') == 1:
                record.is_time_editable = True

    @api.depends('inventory_id')
    def _compute_original_shipping_line(self):
        for record in self:
            record.original_shipping_line = ''
            if record.container_id:
                container_id = self.env['container.master'].search([('name', '=', record.container_id.name)])
                if container_id:
                    record.original_shipping_line = record.container_id.shipping_line_id.shipping_line_name

    @api.depends('move_in_id')
    def _compute_move_in_url(self):
        for record in self:
            if record.move_in_id:
                move_in_id = record.move_in_id
                url = '/web#id=%s&model=%s' % (move_in_id.id, 'move.in')
                record.move_in_url = '<a href="%s">%s</a>' % (
                    url, move_in_id.container)
            else:
                record.move_in_url = '#'

    @api.depends('delivery_order_id')
    def _compute_delivery_order_url(self):
        for record in self:
            if record.delivery_order_id:
                delivery_order = record.delivery_order_id
                url = '/web#id=%s&model=%s' % (delivery_order.id, 'delivery.order')
                record.delivery_order_url = '<a href="%s">%s</a>' % (
                url, delivery_order.delivery_no)
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

    @api.depends('booking_validity_datetime','validity_datetime')
    def _compute_validity_status(self):
        today = fields.Date.today()
        for record in self:
            if record.booking_validity_datetime or record.validity_datetime:
                validity_date = fields.Date.from_string(record.booking_validity_datetime) or fields.Date.from_string(record.validity_datetime)
                if validity_date < today:
                    record.validity_status = 'Expired'
                else:
                    record.validity_status = ''
            else:
                record.validity_status = ''

    @api.depends('location_id')
    def _compute_delivery_domain(self):
        """
        Compute the container number domain based on locations and
        move in records.
        """
        for record in self:
            if record.location_id:
                get_do_numbers = self.env['delivery.order'].search([('location', 'in', [record.location_id.id]),
                                                                    ('active', '=', True)]).ids
                move_in_do_numbers = self.env['move.in'].search([('movement_type', 'in', ['import_destuffing', 'factory_return'])]).mapped('do_no_id').ids
                allow_ids = list(set(get_do_numbers) - set(move_in_do_numbers))
                record.delivery_order_compute_domain = [(6, 0, allow_ids)]
            else:
                record.delivery_order_compute_domain = []

    @api.depends('location_id')
    def _compute_booking_domain(self):
        """
        Compute the container number domain based on locations and
        move in records.
        """
        for record in self:
            if record.location_id:
                get_booking_numbers = self.env['vessel.booking'].search([('location', 'in', [record.location_id.id]),
                                                                    ('active', '=', True)]).ids
                move_in_booking_numbers = (self.env['move.in'].search([('movement_type', '=', 'repo')]).
                                      mapped('booking_no_id').ids)
                allow_ids = list(set(get_booking_numbers) - set(move_in_booking_numbers))
                record.vessel_booking_compute_domain = [(6, 0, allow_ids)]
            else:
                record.vessel_booking_compute_domain = []

    @api.onchange('truck_number')
    def _onchange_truck_number(self):
        if self.truck_number:
            self.truck_number = self.truck_number.upper()

    @api.onchange('wagon_number')
    def _onchange_wagon_number(self):
        if self.wagon_number:
            self.wagon_number = self.wagon_number.upper()

    @api.constrains('release_container')
    def action_release_container(self):
        """Updates container status and deletes related hold.release records based on release_container value.
        """
        for record in self:
            if record.container_id and record.release_container == 'yes_release':
                hold_release_container_id = self.env['hold.release.containers'].search(
                    [('container_id', '=', record.container_id.id)])
                if hold_release_container_id:
                    record.inventory_id.write({'hold_release_status': 'release'})
                    hold_release_container_id.unlink()
            elif record.release_container == 'cancel':
                if record.is_container_on_hold:
                    raise ValidationError(_("The Container No. is on hold please select another container or release this container"))

    @api.depends('location_id')
    def _compute_field_visibility_required(self):
        for record in self:
            if record.location_id:
                settings = record.location_id.movement_move_out_settings_ids
                visible_fields = {setting.field_name_move_out.name: setting.show_on_screen for setting in settings}
                record.field_visibility = visible_fields
                required_fields = {setting.field_name_move_out.name: setting.mandatory == 'yes' for setting in settings}
                record.field_required = required_fields
            else:
                record.field_visibility = {}
                record.field_required = {}

    @api.constrains('seal_no_1', 'seal_no_2')
    def _check_seal_numbers(self):
        """Validates that `seal_no_1` and `seal_no_2` are distinct and updates their `rec_status` to 'used'.
        """
        for record in self:
            if record.seal_no_1 and record.seal_no_2 and record.seal_no_1.id == record.seal_no_2.id:
                raise ValidationError(_("Seal Number 1 and Seal Number 2 cannot be the same."))
            if record.seal_no_1:
                record.seal_no_1.write({
                    'rec_status': 'used',
                    'container_number': record.container_id.name
                })
            if record.seal_no_2:
                record.seal_no_2.write({
                    'rec_status': 'used',
                    'container_number': record.container_id.name
                })

            shipping_line = self._get_shipping_line(record.shipping_line_id.id,
                                                    record.location_id.id)

            if shipping_line and shipping_line.seal_threshold is not None:
                available_seal_count = self._get_available_seal_count(
                    record.location_id.id,
                    record.shipping_line_id.id
                )

                if available_seal_count <= int(shipping_line.seal_threshold):
                    shipping_line.email_sent_on = datetime.now()

                    ctx = self._prepare_email_context(shipping_line, record.location_id,
                                                      available_seal_count)
                    mail_template = self.env.ref(
                        'empezar_move_out.email_template_balance_seal_number')
                    mail_template.with_context(ctx).send_mail(record.id, force_send=True,
                                                              raise_exception=True)

    def _compute_move_out_check_active_records(self):
        """Update record status based on the 'active' field.
           Sets the 'rec_status' field to 'active' if 'active' is True,
           otherwise sets it to 'disable'.
        """
        for rec in self:
            if rec.active:
                rec.rec_status = "active"
            else:
                rec.rec_status = "disable"

    @api.depends('location_id')
    def _compute_make_mode_readonly(self):
        """Sets `is_mode_readonly` based on the `location_id` mode and updates `mode` accordingly.
        """
        if self.location_id:
            location_mode = self.location_id.mode_ids.mapped('name')
            if len(location_mode) > 1:
                self.is_mode_readonly = False
            else:
                if 'Rail' in location_mode:
                    self.mode = 'rail'
                else:
                    self.mode = 'truck'
                self.is_mode_readonly = True
        else:
            self.is_mode_readonly = False

    @api.depends('location_id')
    def _compute_make_laden_status_readonly(self):
        """Sets `is_laden_status_readonly` based on the `location_id` mode and updates `mode` accordingly.
        """
        if self.location_id:
            location_laden_status = self.location_id.laden_status_ids.mapped('name')
            if len(location_laden_status) > 1:
                self.is_laden_status_readonly = False
                if 'Laden' in location_laden_status and 'Empty' in location_laden_status :
                    self.laden_status = 'empty'
            else:
                if 'Laden' in location_laden_status:
                    self.laden_status = 'laden'
                else:
                    self.laden_status = 'empty'
                self.is_laden_status_readonly = True
        else:
            self.is_laden_status_readonly = False

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

    @api.onchange('gross_wt', 'tare_wt')
    @api.constrains('gross_wt', 'tare_wt')
    def onchange_gross_and_tare_weight(self):
        """
        Tare weight and gross weight validations.
        """
        self.ensure_one()
        if (self.gross_wt and self.gross_wt < 0) or (self.tare_wt and self.tare_wt < 0):
            raise ValidationError(_('Negative weight is not allowed'))
        if self.gross_wt and self.tare_wt and self.gross_wt < self.tare_wt:
            raise ValidationError(_('Tare weight cannot be greater than gross weight'))

    @api.onchange('mode')
    @api.constrains('mode')
    def changes_in_mode(self):
        """Resets  fields based on the selected mode."""
        self.ensure_one()
        if self.mode:
            if self.mode == 'truck':
                self.rake_number = False
                self.wagon_number = False
                self.stack = False
            else:
                self.truck_number = False
                self.driver_name = False
                self.driver_mobile_number = False
                self.driver_licence_no = False
                self.transporter_allocated_id = False
                self.transporter_fulfilled_id = False

    @api.onchange('temperature')
    @api.depends('inventory_id')
    def _compute_check_temperature_validations(self):
        """Validates temperature and sets is_temperature flag based on container type."""
        for record in self:
            record.is_temperature = False
            if record.container_id:
                if record.container_id.type_size.is_refer == 'yes':
                    record.is_temperature = True
                if not self._is_shipping_line_valid():
                    record.is_temperature = False
                    return
            if not (0 <= record.temperature <= 999):
                raise ValidationError(_("The value of 'temperature' must be between 0 and 999."))

    @api.onchange('humidity')
    @api.depends('inventory_id')
    def _compute_check_humidity_validations(self):
        """Validates humidity and sets is_humidity flag based on container type."""
        for record in self:
            record.is_humidity = False
            if record.container_id:
                if record.container_id.type_size.is_refer == 'yes':
                    record.is_humidity = True
                if not self._is_shipping_line_valid():
                    record.is_humidity = False
                    return
            if not (0 <= record.humidity <= 999):
                raise ValidationError(_("The value of 'humidity' must be between 0 and 999."))

    @api.onchange('vent')
    @api.depends('inventory_id')
    def _compute_check_vent_validations(self):
        """Validates vent and sets is_vent flag based on container type."""
        for record in self:
            record.is_vent = False
            if record.container_id:
                if record.container_id.type_size.is_refer == 'yes':
                    record.is_vent = True
                if not self._is_shipping_line_valid():
                    record.is_vent = False
                    return
            if not (0 <= record.vent <= 999):
                raise ValidationError(_("The value of 'vent' must be between 0 and 999."))

    @api.depends('inventory_id')
    def _compute_check_vent_seal_no_validations(self):
        """Sets is_vent_seal_number flag based on container type and vent seal number."""
        for record in self:
            record.is_vent_seal_number = False
            if record.container_id:
                if record.container_id.type_size.is_refer == 'yes':
                    record.is_vent_seal_number = True
                if not self._is_shipping_line_valid():
                    record.is_vent_seal_number = False
                    return

    @api.onchange('inventory_id')
    @api.constrains('inventory_id')
    def check_container_number_validations(self):
        """Validates container number and its compatibility with location and shipping line requirements."""
        self.ensure_one()

        if not self.container_id:
            return

        # Search for the container from container master.
        master_data = self.env['container.master'].search([
            ('name', '=', self.container_id.name)
        ], limit=1)

        if not master_data:
            raise ValidationError(_('This container number is not available in inventory'))

        if not self.location_id:
            return
        self.check_container_on_hold()
        # container_shipping_line_id = master_data.shipping_line_id
        # container_type_size = master_data.type_size.id
        # if container_type_size:
        #     type_size_obj = self.env['container.type.data'].browse(container_type_size).exists()
        #     if type_size_obj and type_size_obj.is_refer == 'no':
        #         raise ValidationError(
        #             _("No refer containers are allowed to be moved out %s") % self.location_id.name)
        #
        # # Fetch all relevant shipping lines for the location
        # location_shipping_lines = self.location_id.shipping_line_mapping_ids.mapped(
        #     'shipping_line_id')
        #
        # if container_shipping_line_id not in location_shipping_lines:
        #     return
        #
        # # Search once for the location's shipping line mappings
        # mapping_shipping_line_obj = self.env['location.shipping.line.mapping'].search([
        #     ('company_id', '=', self.location_id.id),
        #     ('shipping_line_id', '=', container_shipping_line_id.id)
        # ], limit=1)
        #
        # if not mapping_shipping_line_obj:
        #     return
        #
        # # Check for the condition in the mapped shipping line object
        # if 'Move Out' in mapping_shipping_line_obj.gate_pass_ids.mapped('name') and \
        #         mapping_shipping_line_obj.refer_container == 'no':
        #     raise ValidationError(
        #         _("No refer containers are allowed to be moved out %s") % self.location_id.name)

    def check_container_on_hold(self):
        for record in self:
            if record.container_id:
                container_id = self.env['container.master'].search([('name','=', record.container_id.name)])
                hold_release_id = self.env['hold.release.containers'].search(
                    [('container_id', '=', container_id.id)])
                if hold_release_id:
                    hold_reason = hold_release_id.hold_reason_id.name
                    if hold_reason != 'Reserve for Party':
                        raise ValidationError(_(f'The container no. entered is on Hold for {hold_reason}. Kindly release the container no.'))

    @api.onchange('driver_mobile_number')
    @api.constrains('driver_mobile_number')
    def check_drive_mobile_no_validations(self):
        """Validates driver mobile number to ensure it is 10 digits long and numeric if mode is
        'truck'."""
        if self.mode == 'truck':
            if self.driver_mobile_number and len(self.driver_mobile_number) != 10:
                raise ValidationError(_('Driver mobile no. should be 10 digits only.'))
            if self.driver_mobile_number and not self.driver_mobile_number.isdigit():
                raise ValidationError(_('Only numeric values are allowed'))


    @api.constrains('delivery_order_id')
    def _check_delivery_order_id(self):
        """Validates that the delivery order has a non-zero balance of containers.
        """
        for record in self:
            if record.delivery_order_id and not record.delivery_order_id.active:
                raise ValidationError(_('%s is not active. Please choose an active DO.')
                                      % record.delivery_order_id.delivery_no)
            if record.delivery_order_id and record.delivery_order_id.balance_containers == 0:
                raise exceptions.ValidationError(_("There is no balance quantity in this "
                                                   "DO/Booking. To update this go to record. "
                                                   "Alternatively Choose another record"))

    @api.onchange('type_size_id')
    def check_container_type_size(self):
        for record in self:
            if record.delivery_order_id:
                if record.type_size_id.name not in record.delivery_order_id.container_details.mapped('container_size_type.name'):
                    raise ValidationError(_("This container size/type is not available for the above selected delivery order."))

    @api.constrains('move_out_date_time')
    def _check_move_out_date_time(self):
        """Ensures that the move-out date/time is not set in the future.
        """
        for record in self:
            if record.move_out_date_time > datetime.now():
                raise exceptions.ValidationError(_("Move Out Date/Time cannot be in the future."))

    def _compute_get_create_record_info(self):
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

    def _compute_get_modify_record_info(self):
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

    @api.constrains('inventory_id')
    def check_validation(self):
        for record in self:
            container_id = self.env['container.master'].search([('name', '=',record.container_id.name)])
            existing_move_out = self.env['move.out'].search([('active', '=', True),('location_id', '=', record.location_id.id),
                                                             ('container_id', '=', record.container_id.id),
                                                             ('id', '!=', record.id)])
            if existing_move_out:
                existing_move_out_count = len(existing_move_out)
                existing_move_in = self.env['move.in'].search([('location_id', '=', record.location_id.id),
                    ('container', '=', record.container_id.name), ('active', '=', True)
                ])
                existing_move_in_count = len(existing_move_in)
                if not existing_move_in:
                    raise ValidationError(_("The container cannot be moved out as no move in entry "
                                          "is found"))
                elif existing_move_in_count != (existing_move_out_count + 1):
                    raise ValidationError(_("The container cannot be moved out as no move in entry "
                                          "is found"))
            else:
                move_in_count = self.env['move.in'].search_count([('container', '=', record.container_id.name),('location_id', '=', record.location_id.id)])
                if move_in_count <= 0:
                    raise UserError(_(
                        "You cannot create a Move Out record without at least one Move In record for this container."))

            if record.delivery_order_id:
                delivery_order_id = self.env['delivery.order'].search([('id', '=', record.delivery_order_id.id)])
                if delivery_order_id:
                    matching_container_details = delivery_order_id.container_details.filtered(
                        lambda detail: detail.container_size_type == record.container_id.type_size
                    )
                    if matching_container_details:
                        matching_container_details.balance_container -= 1
            if record.booking_no_id:
                booking_order_id = self.env['vessel.booking'].search([('id', '=', record.booking_no_id.id)])
                if booking_order_id:
                    matching_container_details = booking_order_id.container_details.filtered(
                        lambda detail: detail.container_size_type == record.container_id.type_size
                    )
                    if matching_container_details:
                        matching_container_details.balance -= 1

    # def write(self, vals):
    #     """Overrides write method to perform additional validation when 'active' field is
    #     updated."""
    #     res = super().write(vals)
    #     if 'active' in vals and vals['active']:
    #         self.check_validation()
    #     return res

    def gate_pass(self):
        """
        Pass
        :return:
        """
        for record in self:
            # Check if Gate Pass Number is already set
            if not record.gate_pass_no:
                # Generate the Gate Pass number
                prefix = "GPMO2324"
                location_code = record.location_id.location_code
                sequence = self.env['ir.sequence'].next_by_code('move.out') or _("New")
                gate_pass_number = f"{prefix}{location_code}{sequence}"
                record.write({'gate_pass_no': gate_pass_number})

            return self.env.ref('empezar_move_out.move_out_report_action').report_action(self)

    def _get_report_file_name(self):
        for record in self:
            get_company = self.env['res.company'].search([('parent_id', '=', False), ('active', '=', True)], limit=1)
            company_format = get_company.date_format
            local_tz = pytz.timezone('Asia/Kolkata')
            local_dt = pytz.utc.localize(record.move_out_date_time).astimezone(local_tz)
            date_formats = {
                'DD/MM/YYYY': '%d/%m/%Y',
                'YYYY/MM/DD': '%Y/%m/%d',
                'MM/DD/YYYY': '%m/%d/%Y'
            }
            move_out_date = local_dt.strftime(date_formats.get(company_format, '%d/%m/%Y'))
            move_out_time =local_dt.strftime('%I:%M %p')
            formatted_time = move_out_time.replace('AM', '_AM').replace('PM', '_PM')
            file_name = f"GATEPASS_{record.container_id.name}_{move_out_date}_{formatted_time}"
            return file_name

    def view_edi(self):
        for record in self:
            # Fetch the edi.logs record where move_in_ids contains the current move.in record
            edi_log = self.env['edi.logs'].search([
                ('move_out_ids', 'in', record.ids),
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
                    'domain': [('move_out_ids', '=', self.id)],
                    'views': [(self.env.ref('empezar_edi.edi_logs_tree_view').id, 'tree')],
                    'target': 'new',  # Open the form in a pop-up window
                }
            else:
                # Handle the case where no matching edi.logs record is found
                pass

    def _get_available_seal_count(self, location_id, shipping_line_id):
        """Returns the count of available seals based on location and shipping line."""
        return self.env['seal.management'].search_count([
            ('location', '=', location_id),
            ('shipping_line_id', '=', shipping_line_id),
            ('rec_status', '=', 'available'),
        ])

    def _get_shipping_line(self, shipping_line_id, company_id):
        """Fetches the shipping line mapping record."""
        return self.env['location.shipping.line.mapping'].search([
            ('shipping_line_id', '=', shipping_line_id),
            ('company_id', '=', company_id)
        ], limit=1)

    def _prepare_email_context(self, shipping_line, location, available_seal_count):
        """Prepares the context for sending an email."""
        company_id = self.env['res.company'].search([('active', '=', True),('parent_id', '=', False)], limit=1)
        company_date_format = company_id.date_format or '%Y-%m-%d'
        now = datetime.now()
        format_map = {
            'DD': '%d',
            'MM': '%m',
            'YYYY': '%Y',
        }

        python_date_format = company_date_format
        for key, value in format_map.items():
            python_date_format = python_date_format.replace(key, value)

        current_date = now.strftime(python_date_format)

        return {
            'email_to': shipping_line.to_email,
            'email_from': shipping_line.from_email,
            'email_cc': shipping_line.cc_email,
            'current_date': current_date,
            'available_seal_count': available_seal_count,
            'location_address': self._format_location_address(location),
            'contact': location.phone or '',
            'email': location.email or '',
        }

    def _format_location_address(self, location):
        """Formats the location address."""
        return ', '.join(filter(None, [
            location.street or '',
            location.street2 or '',
            location.city or '',
            location.state_id.name or '',
            location.zip or ''
        ]))

    def download_gate_pass(self):
        for record in self:
            if not record.gate_pass_no:
                raise ValidationError(_("The gate pass has not been generated. Please generate the gate pass."))
            else:
                return self.env.ref('empezar_move_out.move_out_report_action').report_action(self)

    def download_out_edi(self):
        """Pass
        :return:
        """
        if self.edi_out_attachment_id:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s?download=true' % self.edi_out_attachment_id.id,
                'target': 'self',
            }
        else:
            raise ValidationError('No attachment found to download.')

    def download_repair_edi(self):
        """Pass
        :return:
        """
        pass

    @api.onchange('inventory_id', 'booking_no_id')
    @api.constrains('booking_no_id')
    def validation_container_booking(self):
        for record in self:
            if record.movement_type == 'repo':
                if record.booking_no_id and record.container_id:
                    booking_containers = self.env['vessel.booking'].search([('id', '=', record.booking_no_id.id)]).mapped('container_numbers.name')
                    container_numbers = {name.split(' ')[0] for name in booking_containers}
                    if record.container_id.name not in container_numbers:
                        raise ValidationError(_(
                            f"{record.container_id.name} is not present in the Vessel Booking"
                        ))

                    # Check the is_unlink_non_editable flag for all container_numbers
                    container_is_unlinked = record.booking_no_id.container_numbers.filtered(
                        lambda c: c.name.split(' ')[0] == record.container_id.name and c.is_unlink_non_editable
                    )

                    if container_is_unlinked:
                        raise ValidationError(
                            _("Container number cannot be moved out as it is unlinked for the above vessel booking."))

    @api.constrains('booking_no_id')
    def check_active_and_balance_validations(self):
        for record in self:
            if record.booking_no_id and not record.booking_no_id.active:
                raise ValidationError(_('%s is not active. Please choose an active vessel booking.')
                                      % record.booking_no_id.booking_no)
            if record.booking_no_id and record.booking_no_id.balance_containers == 0:
                raise exceptions.ValidationError(_("There is no balance quantity in this "
                                                   "DO/Booking. To update this go to record. "
                                                   "Alternatively Choose another record"))

    @api.onchange('inventory_id')
    def check_container(self):
        """Checks the selected container's status and updates related fields based on its
           hold/release status and associated move-in record.
        """
        for record in self:
            if record.container_id:
                record.shipping_line_id = record.container_id.shipping_line_id.id
                hold_release_id = self.env['hold.release.containers'].search(
                    [('container_id', '=', record.container_id.id)])
                if hold_release_id:
                    hold_reason = hold_release_id.hold_reason_id.name
                    if hold_reason == 'Reserve for Party':
                        record.is_container_on_hold = True
                    else:
                        record.is_container_on_hold = False
                else:
                    record.is_container_on_hold = False

                get_latest_move_in = self.env['move.in'].search(
                    [('container', '=', record.container_id.name)], order='id desc', limit=1)
                if get_latest_move_in:
                    record.move_in_id = get_latest_move_in.id
                    record.created_by_id = get_latest_move_in.create_uid.id
                    record.move_in_date_time = get_latest_move_in.move_in_date_time

    @api.onchange('location_id')
    def on_change_location_id(self):
        """Empty whole records while location is changed.
        """
        if self._context.get('is_location_change'):
            model_fields = self.fields_get()
            exclude_fields = ['id', 'create_date', 'write_date', 'create_uid', 'write_uid',
                              'location_id','is_time_editable']

            for field_name, field_info in model_fields.items():
                if field_name not in exclude_fields:
                    if field_info.get('store', True):
                        setattr(self, field_name, False)

    @api.depends('inventory_id')
    def _compute_display_name(self):
        """Computes and sets the display name based on the container's name and company size type code."""
        for record in self:
            if record.container_id:
                if record.container_id.type_size.company_size_type_code:
                    record.display_name = f' {record.container_id.name}({record.container_id.type_size.company_size_type_code})' if record.container_id else ''
                else:
                    record.display_name = record.container_id.name
            else:
                record.display_name = False

    @api.onchange('movement_type', 'export_stuffing_to', 'repo_to')
    def on_change_movement_type(self):
        """Empty other records based on movement type and related attributes."""
        for record in self:
            clear_fields = {
                "export_stuffing": {
                    'to_port_id': False,
                    'to_terminal_id': False,
                    'to_empty_yard_id': False,
                    'to_cfs_icd_repo_id': False,
                    'repo_to': False,
                    'booking_no_id': False,
                    'to_factory': None if record.export_stuffing_to == 'factory' else False,
                    'to_cfs_icd_id': None if record.export_stuffing_to == 'CFS/ICD' else False
                },
                "repo": {
                    'to_factory': False,
                    'to_cfs_icd_id': False,
                    'export_stuffing_to': False,
                    'delivery_order_id': False,
                    'to_port_id': None if record.repo_to == 'port_terminal' else False,
                    'to_terminal_id': None if record.repo_to == 'port_terminal' else False,
                    'to_cfs_icd_repo_id': None if record.repo_to == 'CFS/ICD' else False,
                    'to_empty_yard_id': None if record.repo_to == 'empty_yard' else False
                }
            }

            # Reset fields based on the movement type
            if record.movement_type in clear_fields:
                for field, value in clear_fields[record.movement_type].items():
                    setattr(record, field, value)

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
            record.booking_balance_and_type_sizes = combined_str

    @api.depends('delivery_order_id')
    def _compute_delivery_order_balance_containers(self):
        """Computes and updates the balance and size types of containers associated with the
        delivery order.
        """
        for record in self:
            combined_str = ""
            for container in record.delivery_order_id.container_details:
                container_size_type_code = container.container_size_type.company_size_type_code
                balance = container.balance_container
                combined_entry = f"{container_size_type_code} (* {balance})"
                if combined_str:
                    combined_str += " , "
                combined_str += combined_entry
            record.delivery_order_balance_and_type_sizes = combined_str

    @api.onchange('booking_no_id', 'delivery_order_id')
    def onchange_delivery_booking_no(self):
        """Updates transporter and exporter fields based on the selected booking or delivery order."""
        for record in self:
            if record.booking_no_id:
                transporter = record.booking_no_id.transporter_name
                if transporter:
                    record.transporter_allocated_id = transporter
            elif record.delivery_order_id:
                exporter = record.delivery_order_id.exporter_name
                if exporter:
                    record.exporter_name_id = exporter
            else:
                record.transporter_allocated_id = False
                record.exporter_name_id = False

    @api.depends('location_id')
    def _compute_gate_pass_visibility(self):
        for record in self:
            if record.location_id:
                # Fetch the shipping lines based on the location_id
                shipping_lines = record.location_id.shipping_line_mapping_ids.mapped('shipping_line_id')
                if shipping_lines and record.shipping_line_id in shipping_lines:
                    val = record.location_id.shipping_line_mapping_ids.filtered(
                        lambda act: act.shipping_line_id == record.shipping_line_id)
                    if 'Move Out' in val.gate_pass_ids.mapped('name'):
                        record.gate_pass_visible = True
                    else:
                        record.gate_pass_visible = False
                else:
                    record.gate_pass_visible = False

    @api.constrains(
        'transporter_allocated_id',
        'transporter_fulfilled_id',
        'exporter_name_id',
        'cha_name_id',
        'billed_to_party',
        'location_id',
        'shipping_line_id'
    )
    def check_record_is_active_or_not(self):
        """
        Check the mentioned record is active or not.
        """
        self.ensure_one()

        # Dictionary to map field names to their respective display attributes and error messages
        field_mapping = {
            'transporter_allocated_id': ('party_name', _('Please choose an active party.')),
            'transporter_fulfilled_id': ('party_name', _('Please choose an active party.')),
            'exporter_name_id': ('party_name', _('Please choose an active party.')),
            'cha_name_id': ('party_name', _('Please choose an active party.')),
            'billed_to_party': ('party_name', _('Please choose an active party.')),
            'location_id': ('name', _('Please choose an active location.')),
            'shipping_line_id': ('shipping_line_name', _('Please choose an active shipping line.')),
        }
        for field_name, (display_field, error_msg) in field_mapping.items():
            field = getattr(self, field_name)
            if field and not field.active:
                raise ValidationError(_('%s is not active. %s') % (getattr(field, display_field), error_msg))

    @api.model
    def get_edit_move_out_popup_message(self, move_out_id):
        """
        This method is called from js file to open edit pop-up conditionally.
        """
        if not move_out_id:
            return False

        move_out_obj = self.env['move.out'].browse(move_out_id)

        if not move_out_obj.exists():
            return False

        is_gate_pass_generated = False
        is_edi_generated = False
        is_repair_edi_generated = False

        shipping_line = move_out_obj.shipping_line_id
        location = move_out_obj.location_id

        # Check if there are any active shipping line mappings for the location
        mapped_shipping_lines = location.shipping_line_mapping_ids.filtered(
            lambda line: line.shipping_line_id == shipping_line and line.active
        )

        # Check if there are any active EDI settings for the location and shipping line
        mapped_move_in_location_edi = self.env['edi.settings'].search(
            [('location', '=', location.id), ('active', '=', True), ('shipping_line_id', '=', shipping_line.id),
             ('edi_type', '=', 'move_in')]
        )

        mapped_repair_location_edi = self.env['edi.settings'].search(
            [('location', '=', location.id), ('active', '=', True), ('shipping_line_id', '=', shipping_line.id),
             ('edi_type', '=', 'repair')]
        )

        # Determine if gate pass has been generated
        if mapped_shipping_lines and any(
                'Move Out' in line.gate_pass_ids.mapped('name') for line in mapped_shipping_lines):
            if move_out_obj.gate_pass_no:
                is_gate_pass_generated = True

        # Determine if EDI has been generated
        if mapped_move_in_location_edi and move_out_obj.is_edi_send:
            is_edi_generated = True

        # Determine if Repair EDI has been generated
        if mapped_repair_location_edi and move_out_obj.is_repair_edi_send:
            is_repair_edi_generated = True

        # Return the result as a dictionary or other format as needed
        return {
            'is_gate_pass_generated': is_gate_pass_generated,
            'is_edi_generated': is_edi_generated,
            'is_repair_edi_generated': is_repair_edi_generated,
        }

    def _is_shipping_line_valid(self):
        """Checks if the container's shipping line is valid for the location."""
        for record in self:
            container_shipping_line_id = record.container_id.shipping_line_id
            location_shipping_lines = record.location_id.shipping_line_mapping_ids.mapped('shipping_line_id')

            if container_shipping_line_id not in location_shipping_lines:
                return False

            mapping_shipping_line_obj = self.env['location.shipping.line.mapping'].search([
                ('company_id', '=', record.location_id.id),
                ('shipping_line_id', '=', container_shipping_line_id.id)
            ], limit=1)

            if mapping_shipping_line_obj and mapping_shipping_line_obj.refer_container == 'no':
                return False

            return True

    def disable_move_out_validations(self):
        if self.inventory_id and self.location_id:
            get_inventory = self.env['container.inventory'].search([('name', '=', self.inventory_id.name),
                                                                    ('location_id', '!=', self.location_id.id)],
                                                                   limit=1)
            if get_inventory:
                raise ValidationError(
                    _('The Move Out Record cannot be disabled as it is present in the inventory of %s location.') % (
                        get_inventory.location_id.name))
        else:
            raise ValidationError(_('No container found.'))


    def update_move_out_balance_containers(self):
        """
        Updates the `balance_containers` value in the associated delivery order when a record is archived.
        """
        if self.delivery_order_id:
            delivery_order = self.delivery_order_id
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
            matching_container = booking_order.container_details.filtered(
                lambda c: c.container_size_type.name == self.type_size_id.name
            )
            if matching_container:
                matching_container.balance += 1
        else:
            raise ValidationError(
                _("No associated booking found for the record."))

    def disable_move_out_invoice_validation(self):
        """Ensures that if there is an existing Invoice record, the active field is set to False."""
        for record in self:
            move_out_invoice_records = self.env['move.in.out.invoice'].search([
                ('move_out_id', '=', record.id)])
            if move_out_invoice_records:
                for invoice in move_out_invoice_records:
                    if invoice.invoice_status == 'active':
                        raise ValidationError(_("The Move Out Record cannot be disabled as active invoices are linked to this Move Out Record."))

    def activate_matching_inventory_record(self):
        """
        Matches the `move_out_date_time`, `move_in_id`, and `move_in_date_time`
        with records in the `container.inventory` model. Activates the record
        if all conditions are met.
        """
        for record in self:
            # Split `move_out_date_time` into date and hour
            move_out_date = record.move_out_date_time.date()
            move_in_date_time = record.move_in_id.move_in_date_time
            move_in_date = move_in_date_time.date()

            # Search for matching record in `container.inventory`
            inventory_record = self.env['container.inventory'].search([
                ('move_in_id', '=', record.move_in_id.id),
                ('move_out_date', '=', move_out_date),
                ('move_in_date', '=', move_in_date),
                ('location_id', '=', self.location_id.id),
                ('active','=', False)], limit=1)
            # Activate the record if all conditions are met
            if inventory_record:
                inventory_record.write({'active': True})
                inventory_record.move_out_date = False
                inventory_record.out_hour = False
                inventory_record.out_minutes = False

    @api.model
    def write(self, vals):
        try:
            if 'active' in vals and vals['active'] == True:
                raise ValidationError(_("You cannot unarchive a record. Please create a new record instead."))
            if 'active' in vals and vals['active'] == False:
                self.disable_move_out_invoice_validation()
                self.disable_move_out_validations()
                self.activate_matching_inventory_record()
                self.update_move_out_balance_containers()
        except Exception as e:
            raise ValidationError(_(e))
        return super(MoveOut, self).write(vals)
