""" -*- coding: utf-8 -*-"""
from datetime import date
from odoo import fields, models, api, _, exceptions
from odoo.addons.empezar_base.models.res_users import ResUsers
from odoo.exceptions import ValidationError
import pytz


class DeliveryOrder(models.Model):
    _name = "delivery.order"
    _description = "Delivery Order"
    _rec_name = 'delivery_no'
    _order = 'id DESC'

    shipping_line_logo = fields.Binary(
        string="Shipping Line", related="shipping_line_id.logo")
    shipping_line_id = fields.Many2one(
        "res.partner",
        string="Shipping Line",
        domain="[('is_shipping_line', '=', True), ('active', '=', True)]",
        required=True
    )
    is_shipping_line = fields.Boolean("Is Shipping Line", default=False)
    delivery_no = fields.Char(string="DO No.", size=32, required=True)
    terminal = fields.Many2one("container.facilities", string='Terminal',
                               domain="[('facility_type', '=', 'terminal')]")
    delivery_date = fields.Date("DO Date", required=True)
    validity_datetime = fields.Datetime("DO Valid Till", required=True)
    exporter_name = fields.Many2one(
        "res.partner", string="Exporter",
        domain="[('parties_type_ids.name', '=', 'Exporter'), ('active', '=', True)]")
    booking_party = fields.Many2one(
        "res.partner", string="Booking Party",
        domain="[('parties_type_ids.name', '=', 'Booking'), ('active', '=', True)]")
    forwarder_name = fields.Many2one(
        "res.partner", string="Forwarder/CHA",
        domain="[('parties_type_ids.name', '=', 'CHA'), ('active', '=', True)]")
    import_name = fields.Many2one(
        "res.partner", string="Importer",
        domain="[('parties_type_ids.name', '=', 'Importer'), ('active', '=', True)]")
    commodity = fields.Char(string="Commodity", size=128)
    cargo_weight = fields.Char(string="Cargo Weight(KGs)", size=12)
    vessel = fields.Char(string="Vessel", size=32)
    voyage = fields.Char(string="Voyage", size=32)
    remark = fields.Char(string="Remarks", size=128)
    port_loading = fields.Many2one(
        'master.port.data',
        string='Port of Loading', domain="[('active', '=', True)]")
    port_discharge = fields.Many2one(
        'master.port.data',
        string='Port of Discharge', domain="[('active', '=', True)]")
    location = fields.Many2many('res.company', string="Location", required=True,
                                domain="[('active', '=', True)]")
    to_from_location = fields.Char("To/From Location" ,size=128)
    stuffing_location = fields.Char("Stuffing Location", size=128)
    # to_from_location = fields.Many2one('res.company', string="To/From Location", domain=[('parent_id', '!=', False)])
    # stuffing_location = fields.Many2one('res.company', string="Stuffing Location")
    total_containers = fields.Integer(string="Total Containers", compute='_get_total_containers')
    balance_containers = fields.Integer(string="Balance Containers", compute='_get_total_balance_container')
    rec_status = fields.Selection(
        [
            ("active", "Active"),
            ("disable", "Disable"),
        ],
        default="active",
        string="Status", compute="_compute_check_active_records")
    active = fields.Boolean(string="Active", default=True)
    display_create_info = fields.Char(compute="_compute_get_create_record_info")
    display_modified_info = fields.Char(compute="_compute_get_modify_record_info")
    display_sources = fields.Char(string="Sources", readonly=True, default="User Entry")
    container_details = fields.One2many("container.details.delivery", "delivery_id")
    display_info = fields.Char(
        string='Delivery Order No./Valid Till Date',
        compute='_compute_display_info',
    )

    @api.depends('container_details')
    def _get_total_containers(self):
        for rec in self:
            rec.total_containers = sum(rec.container_details.mapped('container_qty'))

    @api.depends('container_details')
    def _get_total_balance_container(self):
        for rec in self:
            rec.balance_containers = sum(rec.container_details.mapped('balance_container'))

    @api.constrains('delivery_no', 'shipping_line_id')
    def _check_unique_delivery_no_shipping_line(self):
        for record in self:
            domain = [('delivery_no', '=', record.delivery_no),
                      ('shipping_line_id', '=', record.shipping_line_id.id)]
            existing_record = self.env['delivery.order'].search(domain)
            if len(existing_record) > 1:
                raise ValidationError(_(
                    'The data with the same Delivery Order number for the Shipping Line already exists.'))

    @api.constrains('cargo_weight')
    @api.onchange('cargo_weight')
    def _cargo_weight_numeric_validation(self):
        """This method validates the Cargo Weight entered by the user.
           Raises:
           ValidationError:
              - If the Cargo Weight contains non-numeric characters.
       """
        for rec in self:
            if rec.cargo_weight:
                if not rec.cargo_weight.isdigit():
                    raise ValidationError(_("The Cargo Weight must contain only numeric values."))

    def _compute_check_active_records(self):
        """Update record status based on the 'active' field.
           Sets the 'rec_status' field to 'active' if 'active' is True,
           otherwise sets it to 'disable'.
        """
        for rec in self:
            if rec.active:
                rec.rec_status = "active"
            else:
                rec.rec_status = "disable"

    def update_allocations(self):
        """Return action dictionary to update allocations related to the current delivery order.
           Returns:
                dict: Action dictionary for opening a new window to update allocations.
        """
        return {
            'name': _('Update Allocations'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'update.allocation.wizard',
            'target': 'new',
            'view_id': self.env.ref('empezar_delivery_order.update_allocation_wizard_form_view').id,
            'context': {
                'default_delivery_order_id': self.id,
            },
        }

    def view_allocations(self):
        pass


    @api.depends('delivery_no', 'validity_datetime')
    def _compute_display_info(self):
        """Compute the display name based on delivery number and validity date."""
        for record in self:
            get_company = self.env['res.company'].search([('parent_id', '=', False), ('active', '=', True)], limit=1)
            company_format = get_company.date_format
            if record.validity_datetime:
                local_tz = pytz.timezone('Asia/Kolkata')
                local_dt = pytz.utc.localize(record.validity_datetime).astimezone(local_tz)
                date_formats = {
                    'DD/MM/YYYY': '%d/%m/%Y',
                    'YYYY/MM/DD': '%Y/%m/%d',
                    'MM/DD/YYYY': '%m/%d/%Y'
                }
                formatted_date = local_dt.strftime(date_formats.get(company_format, '%d/%m/%Y'))
                formatted_time = local_dt.strftime('%I:%M %p')
                record.display_info = f"{record.delivery_no} Valid Till: {formatted_date} {formatted_time}"
            else:
                record.display_info = record.delivery_no

    @api.constrains('container_details')
    def _check_container_types_present(self):
        """Check if at least one container detail is selected for each delivery.
           Raises:
            ValidationError: If no container detail is selected.
        """
        for deliver in self:
            if not deliver.container_details:
                raise ValidationError(_("Please select at least one container detail."))

    @api.constrains('delivery_date')
    def _check_delivery_date(self):
        """check delivery Date is valid or not
           :return:
        """
        for record in self:
            if record.delivery_date and record.delivery_date > date.today():
                raise ValidationError(_(
                    "Please select a valid date. Delivery date "
                    "cannot be greater than the current date."))

    @api.constrains('delivery_date', 'validity_datetime')
    def _check_validity_datetime(self):
        """check delivery Date and Validity Date is valid or not
          :return:
        """
        for record in self:
            if record.validity_datetime.date() < record.delivery_date:
                raise ValidationError(_(
                    "Validity date cannot be less than the delivery date."
                    "Please select a future date."))

    def _compute_get_create_record_info(self):
        """Assign create record log string to the appropriate field.
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
        """Assign update record log string to the appropriate field.
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

