from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import xlsxwriter
import base64
import io
import json
import qrcode
from datetime import datetime, timedelta, date
import requests
from io import BytesIO
from .helper import e_invoice_integration
from odoo.addons.empezar_base.models.res_users import ResUsers
import pytz
import re


class MoveInOutInvoice(models.Model):
    _name = "move.in.out.invoice"
    _description = "Invoice Details"
    _rec_name = 'invoice_number'
    _order = "create_date desc"

    move_in_id = fields.Many2one("move.in", string="Move IN",
                                 ondelete="cascade")
    move_out_id = fields.Many2one("move.out", string="Move out",
                                 ondelete="cascade")
    invoice_details = fields.Char("Invoice Details", compute='_compute_invoice_details')
    container_details = fields.Char("Invoice Details")
    invoice_number = fields.Char("Invoice Number")
    invoice_date = fields.Date("Invoice Date", default=fields.Date.context_today)
    billed_to_party = fields.Many2one('res.partner', string="Billed To Party",
                                      domain="[('is_cms_parties', '=', True),('is_this_billed_to_party', '=', 'yes')]")
    party_invoice_type = fields.Char("Party ", compute='_compute_party_invoice_type', store=True)
    billed_to_gst_no = fields.Many2one("gst.details", string="Billed To GST No.",
        domain="[('partner_id', '=', billed_to_party)]")
    billed_to_party_address = fields.Char(" Billed To Party Address", compute='_compute_billed_to_party_address', store=True)
    parties_add_line_1 = fields.Char(string="Parties Address line 1",
                                     related='billed_to_gst_no.parties_add_line_1')
    parties_add_line_2 = fields.Char(string="Parties Address line 2",
                                     related='billed_to_gst_no.parties_add_line_2')
    supply_to_state = fields.Char(related='billed_to_party.gst_state',
                                  string="Supply to State")
    is_gst_applicable = fields.Selection(
        [
            ("yes", "Yes"),
            ("no", "No"),
        ],default='yes',
        string="GST Applicable", required=True)
    invoice_status = fields.Selection(
        [
            ("active", "Active"),
            ("cancelled", "Cancelled"),
        ],
        string="Invoice Status", default="active"
    )
    e_invoice = fields.Selection(
        [
            ("yes", "Yes"),
            ("no", "No"),
        ],string="E Invoice")
    location_id = fields.Many2one('res.company',string="Location")
    currency_id = fields.Many2one("res.currency",related='location_id.currency_id')
    gst_no = fields.Char(string="Billed To GST No.")
    tax_payer_type = fields.Char("TAXPAYER TYPE")
    state_jurisdiction = fields.Char(string="STATE JURISDICTION")
    company_id = fields.Many2one(
        "res.company", string="Company Name", ondelete="cascade"
    )
    nature_of_business = fields.Char("NATURE OF BUSINESS")
    place_of_business = fields.Char("PRINCIPAL PLACE OF BUSINESS")
    additional_place_of_business = fields.Char("ADDITIONAL PLACE OF BUSINESS 1")
    nature_additional_place_of_business = fields.Char(
        "NATURE OF ADDITIONAL PLACE OF BUSINESS 1"
    )
    additional_place_of_business_2 = fields.Char("ADDITIONAL PLACE OF BUSINESS 2")
    nature_additional_place_of_business_2 = fields.Char(
        "NATURE OF ADDITIONAL PLACE OF BUSINESS 2"
    )
    last_update = fields.Char("LAST UPDATE ON")
    gst_api_response = fields.Text(string="GST API Response")
    is_parties_gst_invoice_line_empty = fields.Boolean(
        string="Is GST Invoice Line Empty",
        compute="_compute_is_parties_gst_invoice_line_empty",
        store=True
    )
    gst_state = fields.Char(string="Supply To State")
    payment_mode = fields.Selection(
        [
            ("cash", "Cash"),
            ("online", "Online(NEFT/RTGS/GPAY/PAYTM/UPI/ADVANCE)"),
        ], string="Payment Mode")
    payment_reference = fields.Char(string="Payment Reference", size=32)
    remarks = fields.Char("Remarks", compute='_compute_remarks_display', store=True, readonly=False, size=100)
    is_invoice_locked = fields.Boolean("Is Invoice Locked", default=False)
    move_in_ids = fields.Many2many(
        comodel_name='move.in',
        string='Move In Records'
    )
    move_out_ids = fields.Many2many(
        comodel_name='move.out',
        string='Move Out Records'
    )
    invoice_type = fields.Selection(
        [
            ("lift_off", "Lift Off"),
            ("lift_on", "Lift On"),
            ("Others", "Others"),
        ],string="Invoice Type")
    gst_rate = fields.Many2many(comodel_name="account.tax", compute="_compute_gst_rate", store=True)
    gst_rate_display = fields.Float()
    shipping_line_id = fields.Many2one('res.partner', string="Shipping Line Id")
    shipping_line_logo = fields.Binary(string="Shipping Line Logo", related="shipping_line_id.logo")
    charge_ids = fields.One2many('move.in.out.invoice.charge', 'move_in_out_invoice_id', string="Charges",
                                 compute='_compute_charge_record_ids',store=True)
    other_charge_id = fields.Many2one('product.template',
                                string='Charge',
                                domain="[('active', '=', True),('invoice_type','=', 'Others')]")
    amount = fields.Float("Amount", required=True, default=0)
    gst_breakup_cgst = fields.Float("GST Breakup (CGST)", default=0,  compute='_compute_gst_amounts', store=True)
    gst_breakup_sgst = fields.Float("GST Breakup (SGST)", default=0,  compute='_compute_gst_amounts', store=True)
    gst_breakup_igst = fields.Float("GST Breakup (IGST)", default=0,  compute='_compute_gst_amounts', store=True)
    hsn_code_id = fields.Many2one('master.hsn.code', related='other_charge_id.hsn_code')
    hsn_code = fields.Integer("HSN Code", related='hsn_code_id.code')
    source = fields.Selection(
        [
            ("account", "Account"),
            ("move", "Move In/Move Out"),
        ], string="Payment Mode")
    invoice_types = fields.Char("Invoice")
    total_charge_amount = fields.Float(string="Total Charge Amount",
                                       compute='_compute_total_charge_amount', store=True)
    amount_mode = fields.Char("Amount/Mode", compute='_compute_amount_mode')
    total_amount = fields.Float(string="Total Amount", compute='_compute_total_amount', store=True)
    fiscal_year = fields.Many2one('account.fiscal.year', string="Fiscal Year")
    is_sez = fields.Boolean(string="Is SEZ", compute='_compute_billed_to_gst_no')
    ack_number = fields.Char("Ack No", copy=False)
    ack_date = fields.Datetime("Ack Date", copy=False)
    cancel_irn_date = fields.Datetime("Cancel Date", copy=False)
    irn_no = fields.Char("IRN", copy=False)
    generate_irn_response = fields.Text()
    auth_token = fields.Char("Auth Token")
    irn_status = fields.Selection(
        [
            ("active", "Active"),
            ("cancelled", "Cancelled"),
        ],
        string="IRN Status", store=True, default='active')

    qr_code = fields.Char(string="QR Code", compute="_compute_qr_code")
    jwt_string = fields.Char()
    is_success = fields.Boolean("Is Success", default=False)
    response_error = fields.Char("Error")
    display_create_info = fields.Char(compute="_get_create_record_info")
    display_modified_info = fields.Char(compute="_get_modify_record_info")
    display_sources = fields.Char(string="Source", readonly=True, default="Web")

    @api.depends('charge_ids.charge_id','invoice_type', 'location_id', 'is_gst_applicable')
    def _compute_gst_rate(self):
        for record in self:
            if record.charge_ids and record.invoice_type != 'Others':
                for charge in record.charge_ids:
                    if charge.charge_id.gst_rate:  # Assuming each charge record has a gst_rate field
                        record.gst_rate = charge.charge_id.gst_rate.ids
            if record.invoice_type == 'Others' and record.other_charge_id:
                gst_rate = record.other_charge_id.gst_rate
                record.gst_rate = gst_rate

    @api.onchange('other_charge_id','invoice_type', 'location_id', 'is_gst_applicable')
    def _compute_other_charge_id(self):
        for record in self:
            if record.invoice_type == 'Others' and record.other_charge_id:
                gst_rate = record.other_charge_id.gst_rate
                record.write({'gst_rate': gst_rate})

    @api.constrains('charge_ids')
    def _check_charge_validity(self):
        if self.env.context.get('from_pending_invoice', False):
            # Skip validation if the context flag is set
            return
        for record in self:
            if record.invoice_type != 'Others' :
                if not record.charge_ids:
                    raise ValidationError('Charge must be present and it should be active')
                for charge in record.charge_ids:
                    if charge.amount <= 0 or not charge.charge_id.active:
                        raise ValidationError('Charge must be active and amount must be greater than 0.')

    @api.depends('gst_rate', 'amount', 'location_id', 'supply_to_state', 'is_gst_applicable', 'invoice_type', 'charge_ids')
    def _compute_gst_amounts(self):
        for record in self:
            if record.invoice_type == 'Others':
                cgst = sgst = igst = 0.0
                total_amount = 0.0
                amount = record.amount

                # Iterate over all GST rates
                for gst in record.gst_rate:
                    if gst:
                        tax_rate = gst
                        total_gst_rate = tax_rate.amount
                        cgst_bifurcation = sgst_bifurcation = 0.0
                        # Calculate CGST, SGST, and IGST bifurcation for each GST rate
                        for tax in gst.children_tax_ids:
                            if 'cgst' in tax.name.lower():
                                cgst_bifurcation = tax.amount
                            elif 'sgst' in tax.name.lower():
                                sgst_bifurcation = tax.amount
                        # Calculate CGST and SGST if the supply is within the same state
                        if record.supply_to_state == record.location_id.state_id.name:
                            cgst += (cgst_bifurcation / 100) * amount
                            sgst += (sgst_bifurcation / 100) * amount

                        # Calculate IGST if the supply is outside the state or GST is applicable
                        elif record.supply_to_state != record.location_id.state_id.name or record.is_gst_applicable == 'yes':
                            igst += (total_gst_rate / 100) * amount

                # Update the computed values
                record.gst_breakup_cgst = cgst
                record.gst_breakup_sgst = sgst
                record.gst_breakup_igst = igst
            else:
                pass

    @api.depends('billed_to_gst_no')
    def _compute_billed_to_gst_no(self):
        """set the GST related field values"""
        for record in self:
            if record.billed_to_gst_no:
                record.tax_payer_type = record.billed_to_gst_no.tax_payer_type
                record.state_jurisdiction = record.billed_to_gst_no.state_jurisdiction
                record.company_id = record.billed_to_gst_no.company_id
                record.nature_of_business = record.billed_to_gst_no.nature_of_business
                record.place_of_business = record.billed_to_gst_no.place_of_business
                record.additional_place_of_business = record.billed_to_gst_no.additional_place_of_business
                record.nature_additional_place_of_business = record.billed_to_gst_no.nature_additional_place_of_business
                record.additional_place_of_business_2 = record.billed_to_gst_no.additional_place_of_business_2
                record.nature_additional_place_of_business_2 = record.billed_to_gst_no.nature_additional_place_of_business_2
                record.last_update = record.billed_to_gst_no.last_update
                record.gst_api_response = record.billed_to_gst_no.gst_api_response
                record.gst_state = record.billed_to_party.gst_state

            if record.billed_to_gst_no and record.billed_to_gst_no.nature_of_business == 'Special Economic Zone':
                record.is_sez = True
            else:
                record.is_sez = False

    @api.depends('billed_to_party.parties_gst_invoice_line_ids')
    def _compute_is_parties_gst_invoice_line_empty(self):
        """Condition to check the GST lines present or not in parties"""
        for record in self:
            # Check if `parties_gst_invoice_line_ids` is empty
            record.is_parties_gst_invoice_line_empty = not bool(
                record.billed_to_party.parties_gst_invoice_line_ids)

    @api.constrains('other_charge_id', 'amount')
    def _check_amount(self):
        for record in self:
            if record.other_charge_id and record.invoice_type == 'Others' and record.amount <= 0:
                raise ValidationError("Amount must be greater than 0. Please enter a valid amount.")

    @api.depends('charge_ids')
    def _check_charge_ids(self):
        for record in self:
            inactive_charges = record.charge_ids.filtered(lambda charge: not charge.charge_id.active)
            if record.invoice_type != 'Others' and not record.charge_ids or inactive_charges:
                raise ValidationError("Charge must be present and it should be active")
            if record.invoice_type != 'Others' and any(not charge.amount > 0 for charge in record.charge_ids):
                raise ValidationError("Amount must be greater than 0. Please enter a valid amount.")

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

    @api.depends("billed_to_party.street","billed_to_party.street2")
    def _compute_billed_to_party_address(self):
        for record in self:
            record.billed_to_party_address = ''
            if record.billed_to_party.street or record.billed_to_party.street2:
                record.billed_to_party_address = f"{record.billed_to_party.street} {record.billed_to_party.street2}"

    @api.depends('jwt_string')
    def _compute_qr_code(self):
        for record in self:
            if record.jwt_string:
                qr_image = self.extract_qr_from_string(record.jwt_string)
                if qr_image:
                    record.qr_code = base64.b64encode(qr_image).decode('utf-8')
                else:
                    record.qr_code = False
            else:
                record.qr_code = False

    def extract_qr_from_string(self, jwt_string):
        """Generate a QR code from the JWT string."""
        qr = qrcode.make(jwt_string)

        # Convert the QR code to binary data
        qr_image = self._image_to_binary(qr)

        return qr_image

    def _image_to_binary(self, image):
        """Convert the PIL image to binary data."""
        img_stream = BytesIO()
        image.save(img_stream, format='PNG')  # Save as PNG
        img_stream.seek(0)
        return img_stream.read()


    def set_e_invoice(self, location_id, shipping_line_id):
        location = self.env['res.company'].search([('id', '=', location_id)])
        if location and shipping_line_id:
            matching_setting = location.invoice_setting_ids.filtered(
                lambda setting: setting.inv_shipping_line_id.id == shipping_line_id
            )
            if matching_setting:
                return matching_setting[0].e_invoice_applicable
        return

    # @api.depends('billed_to_gst_no')
    # def _compute_billed_to_gst_no(self):
    #     for record in self:
    #         if record.billed_to_gst_no and record.billed_to_gst_no.nature_of_business == 'Special Economic Zone':
    #             record.is_sez = True
    #         else:
    #             record.is_sez = False

    @api.depends('charge_ids.gst_breakup_cgst', 'charge_ids.gst_breakup_sgst', 'charge_ids.gst_breakup_igst', 'charge_ids.total_amount','other_charge_id','amount')
    def _compute_total_amount(self):
        for record in self:
            if record.invoice_type == 'Others':
                record.total_amount = record.amount + record.gst_breakup_cgst + record.gst_breakup_sgst + record.gst_breakup_igst
            else:
                # Compute total of CGST, SGST, and IGST along with other charges
                record.total_amount = sum(
                    charge.amount + charge.gst_breakup_cgst + charge.gst_breakup_sgst + charge.gst_breakup_igst
                    for charge in record.charge_ids)

    @api.depends('total_charge_amount', 'payment_mode','other_charge_id','amount')
    def _compute_amount_mode(self):
        for record in self:
            if record.invoice_type == 'Others':
                record.amount_mode = f"{record.total_amount}  {record.payment_mode}" if record.amount and record.payment_mode else ""
            else:
                record.amount_mode = f"{record.total_amount}  {record.payment_mode}" if record.total_charge_amount and record.payment_mode else ""

    @api.depends('charge_ids.amount')
    def _compute_total_charge_amount(self):
        for record in self:
            record.total_charge_amount = sum(charge.amount for charge in record.charge_ids)

    @api.depends('move_in_id', 'move_out_id', 'invoice_type')
    def _compute_charge_record_ids(self):
        for record in self:
            move_in = record.move_in_id
            move_out = record.move_out_id
            invoice_type = record.invoice_type
            size = ""
            if invoice_type:
                product_templates = self.env["product.template"].search(
                    [('invoice_type', '=', invoice_type),('active','=',True)]
                )
                for template in product_templates:
                    # Calculate amount and set total_amount to the same value
                    amount = record.set_amount(
                        location_id=move_in.location_id if move_in else move_out.location_id,
                        invoice_type=invoice_type,
                        move_in_id=move_in,
                        move_out_id=move_out
                    )
                    container_type = record.move_in_id.type_size_id if record.move_in_id else record.move_out_id.type_size_id

                    if container_type:
                        size = "20 FT" if container_type.te_us == 1 else "40 FT"

                    # Create the charge record with amount and total_amount set to the same value
                    charge_record = self.env['move.in.out.invoice.charge'].create({
                        'move_in_out_invoice_id': record.id,
                        'charge_id': template.id,
                        'qty': 1,
                        'size' :size,
                        'amount': amount,
                        'total_amount': amount,
                    })
                    self.charge_ids = charge_record
                else:
                    self.charge_ids = []
            else:
                self.charge_ids = []

    @api.model
    def default_get(self, fields):
        """Override default_get to fetch values based on context ID and model."""
        res = super().default_get(fields)
        context_params = self._context.get('params', {})
        move_record_id = False
        # move_record_id = context_params.get('id') or self._context.get('default_move_in_id')
        model_name = context_params.get('model') or self._context.get('active_model')
        if model_name == 'move.in':
            move_record_id = context_params.get('id') or self._context.get('default_move_in_id')
        elif model_name == 'move.out':
            move_record_id = context_params.get('id') or self._context.get('default_move_out_id')
        res["source"] = "move"
        if move_record_id and model_name:
            if model_name == 'move.in':
                move_in = self.env['move.in'].browse(move_record_id)
                if move_in.exists():
                    res['location_id'] = move_in.location_id.id
                    res['shipping_line_id'] = move_in.shipping_line_id.id
                    e_invoice = self.set_e_invoice(move_in.location_id.id,move_in.shipping_line_id.id)
                    res['e_invoice'] = e_invoice
                    res['billed_to_party'] = move_in.billed_to_party.id
                    invoice_type = self.set_invoice_type(move_in_id=move_in,move_out_id=None,location_id=move_in.location_id.id)
                    res['invoice_type'] = invoice_type
                    payment_mode = self.set_payment_mode(move_in_id=move_in, move_out_id=None,location_id=move_in.location_id.id)
                    res['payment_mode'] = payment_mode
                    invoice_number = self.set_invoice_number(location_id=move_in.location_id)
                    res['invoice_number'] = invoice_number
            elif model_name == 'move.out':
                move_out = self.env['move.out'].browse(move_record_id)
                if move_out.exists():
                    invoice_type = self.set_invoice_type(move_in_id=None, move_out_id=move_out, location_id=move_out.location_id.id)
                    res['invoice_type'] = invoice_type
                    res['location_id'] = move_out.location_id.id
                    res['shipping_line_id'] = move_out.shipping_line_id.id
                    e_invoice = self.set_e_invoice(move_out.location_id.id,move_out.shipping_line_id.id)
                    res['e_invoice'] = e_invoice
                    res['billed_to_party'] = move_out.billed_to_party.id
                    payment_mode = self.set_payment_mode(move_in_id=move_out, move_out_id=None, location_id=move_out.location_id.id)
                    res['payment_mode'] = payment_mode
                    invoice_number = self.set_invoice_number(location_id=move_out.location_id)
                    res['invoice_number'] = invoice_number
        return res

    @api.depends('invoice_number', 'invoice_date')
    def _compute_invoice_details(self):
        for record in self:
            if record.invoice_date:
                # Get the company format
                get_company = self.env['res.company'].search(
                    [('parent_id', '=', False), ('active', '=', True)], limit=1)
                company_format = get_company.date_format

                # Define date formats
                date_formats = {
                    'DD/MM/YYYY': '%d/%m/%Y',
                    'YYYY/MM/DD': '%Y/%m/%d',
                    'MM/DD/YYYY': '%m/%d/%Y'
                }

                # Format the date based on the company setting
                formatted_invoice_date = record.invoice_date.strftime(
                    date_formats.get(company_format, '%d/%m/%Y'))

                # Create the invoice details with the formatted date
                record.invoice_details = f"{record.invoice_number} {formatted_invoice_date}"
            else:
                record.invoice_details = record.invoice_number

    def get_e_invoice_authentication_token(self):
        """
        This function return e-invoice credentials details.
        :return:
        """
        credentials = self.env["e.invoice.credentials"].search([], limit=1)
        if credentials:
            username= credentials.username or ''
            password= credentials.password or ''
            ip_address= credentials.ip_address or ''
            email = credentials.email or ''
            client_id = credentials.client_id or ''
            client_secret = credentials.client_secret or ''
            gstin = credentials.gstin or ''
            return username, password, ip_address, email, client_id, client_secret, gstin
        return {"error": "GST Credentials Not Found."}

    def charge_record_ids(self,move_in_id, move_out_id, invoice_type):
        move_in = self.env['move.in'].search([('id','=',move_in_id)])
        move_out = self.env['move.in'].search([('id', '=', move_out_id)])
        invoice_type = invoice_type
        size = ""
        if invoice_type:
            product_templates = self.env["product.template"].search(
                [('invoice_type', '=', invoice_type)]
            )
            for template in product_templates:
                amount = self.set_amount(
                    location_id=move_in.location_id if move_in else move_out.location_id,
                    invoice_type=invoice_type,
                    move_in_id=move_in,
                    move_out_id=move_out
                )
                container_type = move_in.type_size_id if move_in else move_out.type_size_id

                if container_type:
                    size = "20 FT" if container_type.te_us == 1 else "40 FT"

                # Create the charge record with amount and total_amount set to the same value
                charge_records = self.env['move.in.out.invoice.charge'].search([
                    ('move_in_out_invoice_id', '=', self.id),
                    ('charge_id', '=', template.id),
                    ('size', '=', size),
                    ('amount', '=', amount)
                ], limit=1)
                return charge_records

    def calculate_gst_rate_value(self,charge_id,vals):
        # Get GST rate names
        gst_rate = 0.0
        if  vals['invoice_type'] == 'Others':
            other_charge_id = vals['other_charge_id']
            charge = self.env['product.template'].search([('id','=', other_charge_id)], limit=1)
            if charge:
                gst_rate_names = charge.gst_rate.mapped('name')
                # Process each GST rate entry
                for rate in gst_rate_names:
                    gst_rate += self._extract_gst_percentage(rate)
            return gst_rate
        else:
            charge = charge_id
            if charge:
                gst_rate_names = charge.charge_id.gst_rate.mapped('name')
                # Process each GST rate entry
                for rate in gst_rate_names:
                    gst_rate += self._extract_gst_percentage(rate)
            return gst_rate

    def _extract_gst_percentage(self, gst_name):
        """
        Helper method to extract GST percentage from the name.
        Handles formats like '18% IGST', '9% CGST', 'GST 18'.
        """
        try:
            # Use regex to find numeric values in the GST name
            match = re.search(r'(\d+(\.\d+)?)', gst_name)  # Matches integers and decimals
            if match:
                return float(match.group(1))  # Extract matched numeric value
        except ValueError:
            pass  # Return 0.0 if conversion fails
        return 0.0  # Default to 0 if no percentage is found

    def prepare_generate_irn(self,location,charge_id,shipping_line_id, billed_party,invoice_number,billed_to_gst_no, vals):
        ValDtls = {
            "AssVal": 0,
            "CgstVal": 0,
            "SgstVal": 0,
            "IgstVal": 0,
            "TotInvVal": 0,
        }
        ItemList = []
        if vals['invoice_type'] == 'Others':
            other_charge_id = vals['other_charge_id']
            gst_breakup_cgst = 0
            gst_breakup_sgst = 0
            gst_breakup_igst = 0
            charge = self.env['product.template'].search([('id', '=', other_charge_id)], limit=1)
            gst_rate = self.calculate_gst_rate_value(charge, vals)
            taxable_value = float(vals['amount'])- (gst_breakup_cgst + gst_breakup_sgst + gst_breakup_igst) if charge else 0.00
            # Calculate IGST using the taxable value and GST rate from the charge
            igst_amount = round(taxable_value * (gst_rate / 100)) if charge else 0.00
            total_item_value = round(float(vals['amount']) + igst_amount + gst_breakup_cgst + gst_breakup_sgst,2)
            total_item_value = f"{total_item_value:.2f}"
            igst_amount_final = f"{igst_amount:.2f}"
            ItemList.append({
                "SlNo": "1",
                "PrdDesc": charge.charge_name,
                "IsServc": "Y",
                "HsnCd": str(charge.hsn_code.code),
                "UnitPrice": float(vals['amount']),
                "TotAmt": float(vals['amount']),
                "AssAmt": float(vals['amount']),
                "GstRt": gst_rate,
                "IgstAmt": igst_amount,
                "CgstAmt": gst_breakup_cgst,
                "SgstAmt": gst_breakup_sgst,
                "TotItemVal": total_item_value,
            })

            ValDtls["AssVal"] = float(vals['amount'])
            ValDtls["CgstVal"] = gst_breakup_cgst
            ValDtls["SgstVal"] = gst_breakup_sgst
            ValDtls["IgstVal"] = igst_amount
            ValDtls["TotInvVal"] = float(vals['amount']) + igst_amount + gst_breakup_cgst + gst_breakup_sgst

        else:
            charge = charge_id
            gst_rate = self.calculate_gst_rate_value(charge, vals)
            taxable_value = float(charge.total_amount if charge else 0.00) - (
                        charge.gst_breakup_cgst if charge else 0.00 + charge.gst_breakup_sgst if charge else 0.00+ charge.gst_breakup_igst if charge else 0.00) if charge else 0.00
            # Calculate IGST using the taxable value and GST rate from the charge
            igst_amount = round(taxable_value * (gst_rate / 100)) if charge else 0.00
            total_item_value = round(
                float(charge.total_amount) + igst_amount + charge.gst_breakup_cgst + charge.gst_breakup_sgst, 2) if charge else 0.00
            total_item_value = f"{total_item_value:.2f}"
            igst_amount_final = f"{igst_amount:.2f}"
            ItemList.append({
              "SlNo": "1",
              "PrdDesc": charge.charge_name  if charge else '',
              "IsServc": "Y",
              "HsnCd":str(charge.charge_id.hsn_code.code) if charge else '' ,
              "UnitPrice": charge.amount if charge else 0,  #doubt written rate as present in charge
              "TotAmt": charge.total_amount if charge else 0,
              "AssAmt": charge.total_amount if charge else 0,
              "GstRt": gst_rate if charge else '',
              "IgstAmt": igst_amount,
              "CgstAmt": charge.gst_breakup_cgst if charge else 0 ,
              "SgstAmt": charge.gst_breakup_sgst if charge else 0,
              "TotItemVal": total_item_value,
            })
            ValDtls["AssVal"] = charge.total_amount if charge else 0
            ValDtls["CgstVal"] = 0
            ValDtls["SgstVal"] = 0
            ValDtls["IgstVal"] = igst_amount
            ValDtls["TotInvVal"] = charge.total_amount + igst_amount + charge.gst_breakup_cgst + charge.gst_breakup_sgst if charge else 0

        location_id = self.env['res.company'].search([('id','=',location)],limit=1)
        billed_to_party = self.env['res.partner'].search([('id', '=', billed_party)], limit=1)
        billed_to_gst_no_id = self.env['gst.details'].search([('id', '=', billed_to_gst_no)], limit=1)
        if billed_to_gst_no_id and billed_to_gst_no_id.nature_of_business == 'Special Economic Zone' and billed_to_gst_no_id.gst_rate:
            sub_type = 'SEZWP'
        elif billed_to_gst_no_id and billed_to_gst_no_id.nature_of_business == 'Special Economic Zone' and not billed_to_gst_no_id.gst_rate:
            sub_type = 'SEZWOP'
        else:
            sub_type = 'B2B'
        current_date = date.today()
        # Format the date and time in IST with AM/PM
        formatted_invoice_date = current_date.strftime("%d/%m/%Y")
        if location_id and shipping_line_id:
            matching_setting = location_id.invoice_setting_ids.filtered(
                lambda setting: setting.inv_shipping_line_id.id == shipping_line_id
            )
            lgname = f'{matching_setting.inv_applicable_at_location_ids.mapped("name")}{matching_setting.inv_shipping_line_id.name}'
        param = {
            "Version": "1.1",
            "TranDtls": {
                "TaxSch": "GST",
                "SupTyp": sub_type,
            },
            "DocDtls": {
                "Typ": "INV",
                "No": invoice_number,
                "Dt": formatted_invoice_date,
            },
            "SellerDtls": {
                "Gstin": matching_setting.gst_number,
                "LglNm": lgname,
                "Addr1": matching_setting.address_line_1,
                "Addr2": matching_setting.address_line_2,
                "Loc": matching_setting.city,
                "Pin": matching_setting.pincode,
                "Stcd": "29", # state code with come here numberic code
            },
            "BuyerDtls": {
                "Gstin": "29AWGPV7107B1Z1", #billed_to_gst_no_id.gst_no, #29AWGPV7107B1Z1
                "LglNm": billed_to_party.party_name,
                "Pos": "12",   #invoice supply to state code will come here
                "Addr1": billed_to_party.street,
                "Addr2": billed_to_party.street2,
                "Loc": billed_to_party.gst_state,
                "Pin": billed_to_party.zip,
                "Stcd": "29", #state code will come here
            },
          "ItemList": ItemList,
          "ValDtls": ValDtls,
          "PrecDocDtls": {
            "InvNo": invoice_number,
            "InvDt": formatted_invoice_date,
          },
        }
        return param

    @api.model
    def authenticate_einvoice_api(self):
        url = "https://api.mastergst.com/einvoice/authenticate"
        username, password, ip_address, email, client_id, client_secret, gstin = self.get_e_invoice_authentication_token()
        if all([username, password, ip_address, email, client_id, client_secret, gstin]):
            headers = {
                "username": username,
                "password": password,
                "ip_address": ip_address,
                "client_id": client_id,
                "client_secret": client_secret,
                "gstin": gstin
            }

            params = {
                "email": email
            }

            try:
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                response_data = response.json()
                return response_data
            except requests.exceptions.RequestException as e:
                print("Error:", e)
                return None
        pass

    def generate_irn(self,auth_token, body_data):
        # Define API URL for generating IRN
        url = "https://api.mastergst.com/einvoice/type/GENERATE/version/V1_03"

        # Fetch required credentials and token
        username, password, ip_address, email, client_id, client_secret, gstin = self.get_e_invoice_authentication_token()
        if all([username, password, ip_address, email, client_id, client_secret, gstin]):
            # Set request headers
            headers = {
                "username": username,
                "password": password,
                "ip_address": ip_address,
                "client_id": client_id,
                "client_secret": client_secret,
                "gstin": gstin,
                "auth-token": auth_token,
                "Content-Type": "application/json"
            }
            # Additional parameters
            params = {
                "email": email
            }
            try:
                # Send POST request with JSON payload
                response = requests.post(url, headers=headers, params=params, json=body_data)

                # Check if the request was successful
                response.raise_for_status()
                response_data = response.json()
                return response_data
            except requests.exceptions.HTTPError as http_err:
                print("HTTP error occurred:", http_err)
                return None
            except requests.exceptions.RequestException as req_err:
                print("Request exception occurred:", req_err)
                return None
        pass

    def e_invoice_integration(self,vals):
        if 'charge_ids' not in vals and (vals.get('move_in_id') or vals.get('move_out_id')):
            charge_record = self.charge_record_ids(vals["move_in_id"], vals["move_out_id"],
                                                        vals["invoice_type"])
            irn_data = self.prepare_generate_irn(location=vals['location_id'],
                                                 charge_id=charge_record,
                                                 shipping_line_id=vals['shipping_line_id'],
                                                 billed_party=vals['billed_to_party'],
                                                 invoice_number=vals['invoice_number'],
                                                 billed_to_gst_no=vals["billed_to_gst_no"], vals=vals)

        if vals['e_invoice'] == 'yes':
            try:
                try:
                    api_response = self.authenticate_einvoice_api()
                # Check if the authentication response is successful
                    if api_response and api_response['status_cd'] == 'Sucess':
                        auth_token = api_response['data'].get('AuthToken')
                        invoice_number = vals['invoice_number']
                        vals['auth_token'] = auth_token
                    else:
                        error_messages = json.loads(api_response['status_desc'])

                        # Prepare a structured output
                        errors = []
                        for error in error_messages:
                            errors.append(
                                f"ErrorMessage: {error['ErrorMessage']}")

                        # Join all error messages into a single string or store them in a field
                        all_errors = "\n".join(errors)
                        vals["response_error"] = all_errors
                except Exception as e:
                    # Handle any exception during IRN generation
                    print(f"Error generating IRN: {e}")

                try:
                    # Generate IRN (Invoice Reference Number)
                    irn_data = self.generate_irn(auth_token, body_data=irn_data)

                    if irn_data and irn_data['status_cd'] == '1':
                        vals['ack_date'] = irn_data['data'].get('AckDt')
                        vals['ack_number'] = irn_data['data'].get('AckNo')
                        vals['irn_no'] = irn_data['data'].get('Irn')
                        vals['jwt_string'] = irn_data['data'].get('SignedQRCode')
                        generate_irn_response = json.dumps(irn_data, indent=4)
                        vals['generate_irn_response'] = generate_irn_response
                        vals["is_success"] = True
                    else:
                        error_messages = json.loads(irn_data['status_desc'])

                        # Prepare a structured output
                        errors = []
                        for error in error_messages:
                            errors.append(
                                f"ErrorMessage: {error['ErrorMessage']}")

                        # Join all error messages into a single string or store them in a field
                        all_errors = "\n".join(errors)
                        vals["response_error"] = all_errors

                except Exception as e:
                    # Handle any exception during IRN generation
                    print(f"Error generating IRN: {e}")
            except KeyError as e:
                # Handle missing keys in the response
                print(f"Error generating IRN: {e}")
        else:
            pass

    def update_billed_party(self, billed_party, vals, gst_no):
        billed_party =  self.env['res.partner'].search([('id','=',billed_party)], limit=1)
        """Set the billed to party  field values for creating party if not here"""
        billed_party.tax_payer_type = vals.get('tax_payer_type')
        billed_party.state_jurisdiction = vals.get('state_jurisdiction')
        billed_party.company_id = vals.get('company_id')
        billed_party.gst_state = vals.get('state')
        billed_party.nature_of_business = vals.get('nature_of_business')
        billed_party.additional_place_of_business = vals.get('additional_place_of_business')
        billed_party.nature_additional_place_of_business = vals.get('nature_additional_place_of_business')
        billed_party.additional_place_of_business_2 = vals.get('additional_place_of_business_2')
        billed_party.nature_additional_place_of_business_2 = vals.get('nature_additional_place_of_business_2')
        billed_party.last_update = vals.get('last_update')
        billed_party.is_gst_applicable = "yes"
        billed_party.parties_gst_invoice_line_ids.gst_no = gst_no
        billed_party.l10n_in_pan = gst_no[2:12]
        billed_party.parties_gst_invoice_line_ids.gst_api_response = vals.get('gst_api_response')

    @api.depends('billed_to_party')
    def _compute_billed_to_party(self):
        """Updates 'billed_to_gst_no' based on the selected 'billed_to_party'
           by searching for related GST records."""
        if self.billed_to_party:
            gst_records = self.env['gst.details'].search(
                [('partner_id', '=', self.billed_to_party.id)])
            if len(gst_records) == 1:
                self.billed_to_gst_no = gst_records[0]
            else:
                self.billed_to_gst_no = False

    def _validate_parties_gst_number(self, gst_no, partner_id=None):
        if len(gst_no) != 15:
            raise ValidationError("GST Number entered should be 15 characters long. Please enter the correct GST Number.")
        if not gst_no.isalnum():
            raise ValidationError("Please enter an alphanumeric GST Number.")
        if partner_id:
            existing_gst_nos = self.env['gst.details'].search(
                [("partner_id", "!=", False),('partner_id','!=',partner_id)]).mapped("gst_no")

            if gst_no in existing_gst_nos:
                raise ValidationError(
                    " GST Number is already set Please enter a different GST Number.")

        return {"success": "true"}

    @api.model
    def create(self, vals):
        move_in_id = vals.get('move_in_id')
        move_out_id = vals.get('move_out_id')
        vals["invoice_date"] = date.today()

        if 'billed_to_party' not in vals:
            # Check if move_out_id is in vals
            if move_out_id:
                move_out = self.env['move.out'].browse(move_out_id)
                if move_out.exists():
                    self.set_container_details(move_in_id=None,move_out_id=move_out)
                    move_out.is_invoice_created = True
                    # Set billed_to_party from move_out record
                    vals['billed_to_party'] = move_out.billed_to_party.id
                    vals['shipping_line_id'] = move_out.shipping_line_id.id

            # Check if move_in_id is in vals
            elif move_in_id:
                move_in = self.env['move.in'].browse(move_in_id)
                self.set_container_details(move_in_id=move_in, move_out_id=None)
                if move_in.exists():
                    move_in.is_invoice_created = True
                    # Set billed_to_party from move_in record
                    vals['billed_to_party'] = move_in.billed_to_party.id
                    vals['shipping_line_id'] = move_in.shipping_line_id.id
        invoice_month = vals["invoice_date"].month
        fiscal_year_id = self.env['account.fiscal.year'].search([('date_from','<=', vals['invoice_date']),('date_to','>=', vals['invoice_date'])],limit=1)
        location = self.env['monthly.lock'].search([
            ('fiscal_year', '=', fiscal_year_id.id),
            ('location_id', '=', vals["location_id"]),
            ('month', '=', invoice_month),
            ('invoice_type', '=', "invoice")
        ], limit=1)

        if location and location.is_locked:
            raise ValidationError(
                "Invoice cannot be created as invoice creation is already locked. Please contact system admin for further support.")
        gst_no = vals.get('gst_no')
        if gst_no:
            if vals['billed_to_party']:
                self.update_billed_party(vals['billed_to_party'], vals, gst_no)
                self._validate_parties_gst_number(gst_no, vals['billed_to_party'])
                gst_detail = self.env['gst.details'].search([
                    ('partner_id', '=', vals['billed_to_party'])
                ], limit=1)
                if gst_detail:
                    vals['billed_to_gst_no'] = gst_detail.id
        try:
            self.e_invoice_integration(vals)
        except KeyError as e:
            print(f"Error generating IRN: {e}")
        return super().create(vals)

    def refresh_invoice(self):
        move_in_out_invoice = self
        e_invoice_integration(move_in_out_invoice)

    def show_error(self):
        return {
            'type': 'ir.actions.act_window',
            'name': f'ERROR - {self.invoice_number}',
            'res_model': 'move.in.out.invoice',
            'view_mode': 'form',
            'views': [(self.env.ref('empezar_account_invoices.error_response_view').id, 'form')],
            'res_id': self.id,
            'target': 'new',
        }

    def write(self, vals):
        invoice_month = self.invoice_date.month
        fiscal_year_id = self.env['account.fiscal.year'].search([('date_from', '<=', self.invoice_date), ('date_to', '>=', self.invoice_date)], limit=1)
        location = self.env['monthly.lock'].search([
            ('fiscal_year', '=', fiscal_year_id.id),
            ('location_id', '=', self.location_id.name),
            ('month', '=', invoice_month),
            ('invoice_type', '=', "invoice")
        ], limit=1)

        if location and location.is_locked:
            raise ValidationError(
                "Invoice cannot be updated as invoice creation is already locked. Please contact system admin for further support.")

        return super().write(vals)

    @api.constrains('move_in_id', 'move_out_id')
    @api.depends('move_in_id', 'move_out_id')
    def set_container_details(self,move_in_id=None,move_out_id=None):
        for record in self:
            if record.move_in_id:
                record.container_details = f"{record.move_in_id.container} {record.move_in_id.type_size_id.company_size_type_code}"
            elif record.move_out_id:
                record.container_details = f"{record.move_out_id.container_id.name} {record.move_out_id.company_size_type}"

    @api.depends('billed_to_party', 'invoice_type','invoice_types')
    def _compute_party_invoice_type(self):
        for record in self:
            if record.source == 'move':
                invoice_type_value = dict(record._fields['invoice_type'].selection).get(
                    record.invoice_type)
            else:
                invoice_type_value = record.invoice_types
            record.party_invoice_type = f"{record.billed_to_party.name} {invoice_type_value}"

    def set_invoice_number(self,location_id):
        """Generate an invoice number based on the specified logic.
        :return: Generated invoice number
        """
        fixed_text = "INV"
        # Location Code of the location for which the invoice is being created
        location_code = location_id.location_code
        fiscal_year = 2324

        # Sequence number incremented each time an invoice is created
        sequence = self.env['ir.sequence'].next_by_code('move.in.out.invoice') or _("New")

        # Generate the invoice number
        invoice_number = f"{fixed_text}{location_code}{fiscal_year}{sequence}"
        return invoice_number

    def set_amount(self,location_id,invoice_type,move_in_id,move_out_id):
        """ Fetch amount of the amount field """
            # Check for Move In scenario
        if invoice_type in ['lift_on', 'lift_off'] and move_in_id:
            lolo_charge = self.env['lolo.charge'].search([
                ('location', '=', move_in_id.location_id.id),
                ('shipping_line', '=', move_in_id.shipping_line_id.id)], limit=1)

            if lolo_charge:
                lolo_charge_lines = lolo_charge.lolo_charge_lines.filtered(
                    lambda line: dict(
                        self.env['lolo.charge.lines']._fields['container_size'].selection).get(
                        line.container_size) == move_in_id.type_size_id.size)

                if lolo_charge_lines:
                    matching_line = lolo_charge_lines[0]
                    if invoice_type == 'lift_off':
                        return matching_line.lift_off
                    elif invoice_type == 'lift_on':
                        return matching_line.lift_on

        # Check for Move Out scenario
        elif invoice_type in ['lift_on', 'lift_off'] and move_out_id:
            lolo_charge = self.env['lolo.charge'].search([
                ('location', '=', location_id.id),
                ('shipping_line', '=', move_out_id.shipping_line_id.id)], limit=1)

            if lolo_charge:
                lolo_charge_lines = lolo_charge.lolo_charge_lines.filtered(
                    lambda line: dict(
                        self.env['lolo.charge.lines']._fields['container_size'].selection).get(
                        line.container_size) == move_out_id.type_size_id.size)
                if lolo_charge_lines:
                    matching_line = lolo_charge_lines[0]
                    if invoice_type == 'lift_off':
                        return matching_line.lift_off
                    elif invoice_type == 'lift_on':
                        return matching_line.lift_on

    @api.model
    def get_payment_mode_dict(self):
        """ Returns a dictionary mapping payment mode keys to their names. """
        return dict(self._fields['payment_mode'].selection)

    def set_payment_mode(self,move_in_id,move_out_id,location_id):
        """Set the payment mode"""
        payment_mode_dict = self.get_payment_mode_dict()  # Get the payment mode dictionary
        payment_modes = []
        # Determine the shipping line ID based on move_in or move_out
        if move_out_id:
            shipping_line_id = move_out_id.shipping_line_id
            # Use the location from the move_out record
            location_id = move_out_id.location_id if move_out_id else False
        elif move_in_id:
            shipping_line_id = move_in_id.shipping_line_id
            # Use the location from the move_in record
            location_id = move_in_id.location_id if move_in_id else False
        else:
            shipping_line_id = None

        # If we have a shipping line ID, fetch applicable payment modes
        if shipping_line_id and location_id:
            for inv_setting in location_id.invoice_setting_ids:
                if inv_setting.inv_shipping_line_id == shipping_line_id:
                    payment_modes += inv_setting.payment_mode_ids.mapped('name')
                    if 'Cash' in payment_modes and 'Online' in payment_modes :
                        matched_keys = ''
                    elif 'Online' in payment_modes:
                        matched_keys = 'online'
                    else:
                        matched_keys = 'cash'
                    return matched_keys
            return False

    def set_invoice_type(self,move_in_id,move_out_id,location_id):
        """ Set the invoice type based on invoice settings."""
        self.invoice_type = False
        if location_id:
            invoice_types = []
            if move_out_id and move_out_id.shipping_line_id:
                for inv_setting in move_out_id.location_id.invoice_setting_ids:
                    if inv_setting.inv_shipping_line_id == move_out_id.shipping_line_id:
                        applicable_types = inv_setting.inv_applicable_at_location_ids.mapped('name')

                        # Check for Lift Off, Lift On, and Others in Move Out
                        if 'Lift Off' in applicable_types:
                            invoice_types.append('lift_off')
                        if 'Lift On' in applicable_types:
                            invoice_types.append('lift_on')
                        if 'Others' in applicable_types:
                            invoice_types.append('others')
                if invoice_types:
                    if 'lift_off' in invoice_types and 'lift_on' in invoice_types:
                        if move_in_id:
                            return 'lift_off'
                        elif move_out_id:
                            return 'lift_on'
                    elif 'lift_off' in invoice_types:
                        return 'lift_off'
                    elif 'lift_on' in invoice_types:
                        return 'lift_on'
                    elif 'others' in invoice_types:
                        return 'Others'

            elif move_in_id and move_in_id.shipping_line_id:
                for inv_setting in move_in_id.location_id.invoice_setting_ids:
                    if inv_setting.inv_shipping_line_id == move_in_id.shipping_line_id:
                        applicable_types = inv_setting.inv_applicable_at_location_ids.mapped('name')

                        # Check for Lift Off, Lift On, and Others in Move In
                        if 'Lift Off' in applicable_types:
                            invoice_types.append('lift_off')
                        if 'Lift On' in applicable_types:
                            invoice_types.append('lift_on')
                        if 'Others' in applicable_types:
                            invoice_types.append('others')
                if invoice_types:
                    if 'lift_off' in invoice_types and 'lift_on' in invoice_types:
                        if move_in_id:
                            return 'lift_off'
                        elif move_out_id:
                            return 'lift_on'
                    elif 'lift_off' in invoice_types:
                        return 'lift_off'
                    elif 'lift_on' in invoice_types:
                        return 'lift_on'
                    elif 'others' in invoice_types:
                        return 'Others'

    def generate_pdf(self):
        """Generate and return a PDF report for the invoice."""
        return self.env.ref('empezar_account_invoices.move_in_out_invoice_report_action').report_action(self)

    @api.onchange('is_gst_applicable')
    @api.depends('is_sez')
    def _compute_remarks_display(self):
        """Set remarks based on GST applicability status."""
        for record in self:
            if record.is_sez:
                if record.is_gst_applicable == 'no':
                    record.remarks = "SUPPLY MEANT FOR EXPORT UNDER LETTER OF UNDERTAKING WITHOUT PAYMENT OF GST"
                elif record.is_gst_applicable == 'yes':
                    record.remarks = (
                        f"EXPORT UNDER LUT BOND. ARN NO. "
                        f"DATED:  (IGST @ IGST AMOUNT: ) "
                        f"SUPPLY MEANT FOR EXPORT UNDER LETTER OF UNDERTAKING WITHOUT PAYMENT OF GST"
                    )
                else:
                    pass

    def cancel_invoice(self):
        """Open a wizard for canceling the invoice with the default invoice ID."""
        if self.e_invoice == 'yes':
            if not self.irn_no:
                raise ValidationError(
                    "E-Invoice has not been generated successfully. Please generate the E-Invoice first."
                )
            elif self.irn_no and self.ack_date:
                e_invoice_create_date = fields.Datetime.to_datetime(self.ack_date)
                current_date_time = fields.Datetime.now()
                time_difference = current_date_time - e_invoice_create_date
                if time_difference > timedelta(hours=24):
                        raise ValidationError(
                            "Invoice cannot be canceled as 24 hours have already passed since GST posting"
                        )
        return {
            'name': 'Cancel Invoice',
            'type': 'ir.actions.act_window',
            'res_model': 'invoice.cancellation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_invoice_id': self.id,
                'default_auth_token': self.auth_token,
                'default_irn_number':self.irn_no
            }
        }

    def e_invoice_record(self):
        """Open a form for creating or editing an E-Invoice with the default invoice ID."""
        if self.ack_date:
            get_company = self.env['res.company'].search([('parent_id', '=', False),
                                                          ('active', '=', True)], limit=1)
            company_format = get_company.date_format or 'DD/MM/YYYY'
            local_tz = pytz.timezone('Asia/Kolkata')
            # Format the date and time
            date_formats = {
                'DD/MM/YYYY': '%d/%m/%Y',
                'YYYY/MM/DD': '%Y/%m/%d',
                'MM/DD/YYYY': '%m/%d/%Y'
            }
            formatted_date = self.ack_date.strftime(date_formats.get(company_format, '%d/%m/%Y'))
            formatted_time = self.ack_date.strftime('%I:%M %p')
            formatted_date_time = f'{formatted_date} {formatted_time}'

            return {
                'name': f'E-Invoice - {self.invoice_number} ',
                'type': 'ir.actions.act_window',
                'res_model': 'e.invoice.wizard',
                'view_mode': 'form',
                'views': [(self.env.ref('empezar_account_invoices.view_e_invoice_wizard').id,
                           'form')],
                'target': 'new',
                'context': {
                    'default_invoice_id': self.id,
                    'default_irn_no':self.irn_no,
                    'default_irn_received_date':self.ack_date,
                    'default_irn_status': self.irn_status,
                    'default_generate_irn_response':self.generate_irn_response,
                    'default_irn_date': formatted_date_time,
                }
            }
        else:
            pass

    def _get_report_filename(self):
        """Generate the filename for the invoice report based on Move In or Move Out details."""
        for record in self:
            if record.move_in_id:
                container_no = record.move_in_id.container if record.move_in_id.container else ''
                invoice_no = record.invoice_number or ''
                move_date = record.move_in_id.move_in_date_time if record.move_in_id.move_in_date_time else ''
                name = f"{container_no}_{invoice_no}_{move_date}"
            elif record.move_out_id:
                container_no = record.move_out_id.container_id.name if record.move_out_id.container_id.name else ''
                invoice_no = record.invoice_number or ''
                move_date = record.move_out_id.move_out_date_time if record.move_out_id.move_out_date_time else ''
                name =  f"{container_no}_{invoice_no}_{move_date}"
            else:
                name = record.invoice_number or ''
            return name

    @api.constrains('billed_to_party')
    def _check_billed_to_party(self):
        """Prevent creating invoices if the 'billed_to_party' is disabled """
        for record in self:
            if record.billed_to_party and not record.billed_to_party.active:
                raise ValidationError(
                    _("The billed-to party is disabled. Please select another party."))

    @api.onchange('billed_to_party')
    def onchange_billed_to_party(self):
        """Updates 'billed_to_gst_no' based on the selected 'billed_to_party' by searching for related GST records."""
        if self.billed_to_party:
            gst_records = self.env['gst.details'].search([('partner_id', '=', self.billed_to_party.id)])
            if len(gst_records) == 1:
                self.billed_to_gst_no = gst_records[0]
            else:
                self.billed_to_gst_no = False

    @api.model
    def action_download_excel(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        active_ids = self.env.context.get('active_ids', [])
        records = self.browse(active_ids)

        # Create sheets
        self._create_detailed_report_sheet(workbook, records)
        self._create_line_wise_summary_sheet(workbook, records)
        self._create_charge_summary_sheet(workbook, records)

        # Close the workbook and prepare for download
        workbook.close()
        output.seek(0)

        # Encode the output to base64 for downloading
        file_data = base64.b64encode(output.read())
        output.close()
        current_date = datetime.now()
        get_company = self.env['res.company'].search([('parent_id', '=', False),
                                                      ('active', '=', True)], limit=1)
        company_format = get_company.date_format
        local_tz = pytz.timezone('Asia/Kolkata')
        local_dt = pytz.utc.localize(current_date).astimezone(local_tz)
        date_formats = {
            'DD/MM/YYYY': '%d/%m/%Y',
            'YYYY/MM/DD': '%Y/%m/%d',
            'MM/DD/YYYY': '%m/%d/%Y'
        }
        formatted_date = local_dt.strftime(date_formats.get(company_format, '%d/%m/%Y'))

        # Create a file record in Odoo
        attachment = self.env['ir.attachment'].create({
            'name': f"Invoice Report {formatted_date}.xlsx",
            'type': 'binary',
            'datas': file_data,
            'store_fname': 'Invoice Report.xlsx',
            'res_model': 'move.in.out.invoice',
            'res_id': False,
        })

        # Return action to download the file
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }

    def _create_detailed_report_sheet(self, workbook,records):
        worksheet1 = workbook.add_worksheet('Detailed Report')

        headers = [
            'Invoice No', 'Invoice Type', 'Location', 'Shipping Line',
            'Container No', 'Billed To Party', 'GST No', 'Supply to State',
            'GST %', 'CGST Amount', 'SGST Amount', 'IGST Amount',
            'Invoice Amount', 'Payment Mode', 'Payment Reference No.'
        ]

        # Create header format with bottom border
        header_format = workbook.add_format({
            'bg_color': '#c9daf8',
            'font_color': 'black',
            'bold': True,
            'border': 1,  # Add border to header cells
        })

        for col_num, header in enumerate(headers):
            worksheet1.write(0, col_num, header, header_format)

        # Create a format for data cells with dark borders
        data_format = workbook.add_format({
            'border': 1,  # Darker border for data cells
        })

        for row_num, record in enumerate(records, start=1):
            container_numbers = self._get_container_numbers(record)
            gst_no = record.billed_to_gst_no.gst_no if record.billed_to_gst_no else ''
            invoice_type = dict(record._fields['invoice_type'].selection).get(
                record.invoice_type) if record.invoice_type else record.invoice_types
            gst_percent = self._get_gst_percent(record)
            cgst_amount, sgst_amount, igst_amount = 0.0, 0.0, 0.0

            payment_reference = record.payment_reference if record.payment_mode != 'cash' else ''

            # Write data for each column
            worksheet1.write(row_num, 0, record.invoice_number or '' ,data_format)
            worksheet1.write(row_num, 1, invoice_type or '' ,data_format)
            worksheet1.write(row_num, 2, record.location_id.name if record.location_id else '' ,data_format)
            worksheet1.write(row_num, 3,
                             record.shipping_line_id.name if record.shipping_line_id else '' ,data_format)
            worksheet1.write(row_num, 4, container_numbers ,data_format)
            worksheet1.write(row_num, 5,
                             record.billed_to_party.name if record.billed_to_party else '' ,data_format)
            worksheet1.write(row_num, 6, gst_no ,data_format)
            worksheet1.write(row_num, 7, record.supply_to_state or '' ,data_format)
            worksheet1.write(row_num, 8, gst_percent ,data_format)
            worksheet1.write(row_num, 9, cgst_amount ,data_format)
            worksheet1.write(row_num, 10, sgst_amount ,data_format)
            worksheet1.write(row_num, 11, igst_amount ,data_format)
            worksheet1.write(row_num, 12, record.total_amount ,data_format)
            worksheet1.write(row_num, 13, record.payment_mode ,data_format)
            worksheet1.write(row_num, 14, payment_reference ,data_format)

        # header_format = workbook.add_format(
        #     {'bg_color': '#c9daf8', 'font_color': 'black', 'bold': True})
        # worksheet1.set_row(0, None, header_format)

        # Set column widths for better visibility
        column_widths = [25, 25, 30, 30, 30, 30, 20, 25, 10, 15, 15, 15, 15, 20, 30]
        for col_num, width in enumerate(column_widths):
            worksheet1.set_column(col_num, col_num, width)

    def _create_line_wise_summary_sheet(self, workbook,records):
        worksheet2 = workbook.add_worksheet('Line Wise Summary')

        # Write headers for Line Wise Summary
        summary_headers = [
            'Shipping Line', 'Date', 'Location', '20 FT', '20 FT Reefer',
            '40 FT', '40 FT Reefer', 'Cash', 'Online', 'Total'
        ]
        header_format = workbook.add_format({
            'bg_color': '#c9daf8',
            'font_color': 'black',
            'bold': True,
            'border': 1,  # Add border to header cells
        })

        data_format = workbook.add_format({
            'border': 1,  # Darker border for data cells
        })

        for col_num, header in enumerate(summary_headers):
            worksheet2.write(0, col_num, header, header_format)

        records = records
        # Aggregate data for summary
        summary_data = self._aggregate_summary_data(records)

        # Write summary data to the second worksheet
        for row_num, (shipping_line, data) in enumerate(summary_data.items(), start=1):
            worksheet2.write(row_num, 0, shipping_line, data_format)
            worksheet2.write(row_num, 1, data['date_str'] ,data_format)
            worksheet2.write(row_num, 2, data['location'] ,data_format)
            worksheet2.write(row_num, 3, data['20 FT'] ,data_format)
            worksheet2.write(row_num, 4, data['20 FT Reefer'] ,data_format)
            worksheet2.write(row_num, 5, data['40 FT'] ,data_format)
            worksheet2.write(row_num, 6, data['40 FT Reefer'] ,data_format)
            worksheet2.write(row_num, 7, data['Cash'] ,data_format)
            worksheet2.write(row_num, 8, data['Online'] ,data_format)
            worksheet2.write(row_num, 9, data['Total'] ,data_format)

        # header_format = workbook.add_format(
        #     {'bg_color': '#c9daf8', 'font_color': 'black', 'bold': True})
        # worksheet2.set_row(0, None, header_format)

        # Set column widths for better visibility in the second sheet
        summary_column_widths = [30, 20, 30, 10, 15, 10, 15, 10, 10, 10]
        for col_num, width in enumerate(summary_column_widths):
            worksheet2.set_column(col_num, col_num, width)

    def _get_container_numbers(self, record):
        # Check if there's only one move_in or move_out record
        if len(record.move_in_ids) == 1:
            return record.move_in_ids.container
        elif len(record.move_out_ids) == 1:
            return record.move_out_ids.container_id.name
        # Existing logic for single or multiple move_in/move_out records
        elif len(record.move_in_ids or record.move_out_ids) <= 1:
            return record.move_in_id.container if record.move_in_id else record.move_out_id.container_id.name
        else:
            return ', '.join(
                record.move_in_ids.mapped('container')) if record.move_in_ids else ', '.join(
                record.move_out_ids.mapped('container_id.name'))

    def _get_gst_percent(self, record):
        gst_rates = record.gst_rate.mapped('name') if record.gst_rate else []
        return ', '.join(map(str, gst_rates)) if gst_rates else '0.00'

    def _count_container_sizes(self, containers):
        size_count = {
            '20 FT': 0,
            '20 FT Reefer': 0,
            '40 FT': 0,
            '40 FT Reefer': 0
        }

        # Loop through containers to count sizes
        for container in containers:
            if container:
                container_size = container.type_size_id.size
                if container_size == '20FT':
                    size_count['20 FT'] += 1
                elif container_size == '20FT Reefer':
                    size_count['20 FT Reefer'] += 1
                elif container_size == '40FT':
                    size_count['40 FT'] += 1
                elif container_size == '40FT Reefer':
                    size_count['40 FT Reefer'] += 1

        return size_count

    def _aggregate_summary_data(self, records):
        summary_data = {}

        for record in records :
            shipping_line = record.shipping_line_id.name if record.shipping_line_id else 'N/A'
            invoice_date = record.invoice_date
            if invoice_date:
                if isinstance(invoice_date, int):
                    base_date = datetime(1899, 12, 30)
                    invoice_date = base_date + timedelta(days=invoice_date)
                date_str = invoice_date.strftime('%d-%m-%Y')
            else:
                date_str = 'N/A'
            location = record.location_id.name if record.location_id else 'N/A'

            if shipping_line not in summary_data:
                summary_data[shipping_line] = {
                    'date_str': date_str,
                    'location': location,
                    '20 FT': 0,
                    '20 FT Reefer': 0,
                    '40 FT': 0,
                    '40 FT Reefer': 0,
                    'Cash': 0,
                    'Online': 0,
                    'Total': 0,
                }

                # List of container-related fields to count sizes from
            container_sources = [record.move_in_ids, record.move_out_ids, record.move_in_id,
                                 record.move_out_id]

            # Count containers for all relevant fields
            for containers in container_sources:
                if containers:
                    size_count = self._count_container_sizes(containers)
                    # Update the summary data with container size counts
                    summary_data[shipping_line]['20 FT'] += size_count['20 FT']
                    summary_data[shipping_line]['20 FT Reefer'] += size_count['20 FT Reefer']
                    summary_data[shipping_line]['40 FT'] += size_count['40 FT']
                    summary_data[shipping_line]['40 FT Reefer'] += size_count['40 FT Reefer']

            # Increment payment method count and amount
            if record.payment_mode == 'cash':
                summary_data[shipping_line][
                    'Cash'] += record.total_amount  # Add total amount to Cash
            elif record.payment_mode == 'online':
                summary_data[shipping_line][
                    'Online'] += record.total_amount  # Add total amount to Online

            # Total count of containers
            summary_data[shipping_line]['Total'] = (
                    summary_data[shipping_line]['Cash'] + summary_data[shipping_line]['Online']
            )

        return summary_data

    def _create_charge_summary_sheet(self, workbook, records):
        worksheet3 = workbook.add_worksheet('Charge Summary')

        lift_off_sub_headers = ['20 FT', '20 FT Reefer', '40 FT', '40 FT Reefer']
        lift_on_sub_headers = ['20 FT', '20 FT Reefer', '40 FT', '40 FT Reefer']

        # Header Formats
        header_format = workbook.add_format(
            {'bg_color': '#c9daf8', 'font_color': 'black', 'bold': True, 'border': 1,})  # Light blue
        lift_off_header_format = workbook.add_format(
            {'bg_color': '#9AC0CD', 'font_color': 'black', 'bold': True, 'border': 1,})  # Blue
        lift_on_header_format = workbook.add_format(
            {'bg_color': '#b6d7a8', 'font_color': 'black', 'bold': True, 'border': 1,})  # Green
        cash_online_total_format = workbook.add_format(
            {'bg_color': '#c9daf8', 'font_color': 'black', 'bold': True, 'border': 1,})
        lift_subheader_total_format = workbook.add_format(
            {'bg_color': 'white', 'font_color': 'black', 'bold': True, 'border': 1,})

        data_format = workbook.add_format({
            'border': 1,  # Darker border for data cells
        })

        # Write headers with specific formats
        worksheet3.write(0, 0, 'Date', header_format)
        worksheet3.write(0, 1, 'Location', header_format)

        worksheet3.merge_range(0, 2, 0, 5, 'Lift OFF', lift_off_header_format)
        worksheet3.merge_range(0, 6, 0, 9, 'Lift ON', lift_on_header_format)

        worksheet3.write(0, 10, 'Cash', cash_online_total_format)
        worksheet3.write(0, 11, 'Online', cash_online_total_format)
        worksheet3.write(0, 12, 'Total', cash_online_total_format)

        # Write headers with specific formats
        worksheet3.write(1, 0, '', lift_subheader_total_format)
        worksheet3.write(1, 1,'', lift_subheader_total_format)

        # Sub Headers
        worksheet3.write_row(1, 2, lift_off_sub_headers, lift_subheader_total_format)
        worksheet3.write_row(1, 6, lift_on_sub_headers, lift_subheader_total_format)

        # Adjustments to create a line underneath Cash, Online, and Total
        worksheet3.write(1, 10, '', lift_subheader_total_format)
        worksheet3.write(1, 11, '', lift_subheader_total_format)
        worksheet3.write(1, 12, '', lift_subheader_total_format)

        # Aggregate and write additional data (sample data used for illustration)
        additional_data = self._aggregate_additional_data(records)
        for row_num, data in enumerate(additional_data, start=2):
            worksheet3.write(row_num, 0, data['date'] ,data_format)
            worksheet3.write(row_num, 1, data['location'] ,data_format)
            worksheet3.write(row_num, 2, data['lift_off']['20 FT'] ,data_format)
            worksheet3.write(row_num, 3, data['lift_off']['20 FT Reefer'] ,data_format)
            worksheet3.write(row_num, 4, data['lift_off']['40 FT'] ,data_format)
            worksheet3.write(row_num, 5, data['lift_off']['40 FT Reefer'] ,data_format)
            worksheet3.write(row_num, 6, data['lift_on']['20 FT'] ,data_format)
            worksheet3.write(row_num, 7, data['lift_on']['20 FT Reefer'] ,data_format)
            worksheet3.write(row_num, 8, data['lift_on']['40 FT'] ,data_format)
            worksheet3.write(row_num, 9, data['lift_on']['40 FT Reefer'] ,data_format)
            worksheet3.write(row_num, 10, data['cash'] ,data_format)
            worksheet3.write(row_num, 11, data['online'] ,data_format)
            worksheet3.write(row_num, 12, data['total'] ,data_format)

        # # # Format header background color
        # # header_format = workbook.add_format(
        # #     {'bg_color': '#c9daf8', 'font_color': 'black', 'bold': True})
        # # worksheet3.set_row(0, None, header_format)
        # for row in range(0, 2):  # Only format the first two rows (headers and sub-headers)
        #     worksheet3.set_row(row, None, header_format if row == 0 else lift_subheader_total_format)

        # Set column widths for better visibility in the third sheet
        additional_column_widths = [15, 30, 10, 15, 10, 15, 10, 15, 10, 15, 10, 10, 10]
        for col_num, width in enumerate(additional_column_widths):
            worksheet3.set_column(col_num, col_num, width)

    def _aggregate_additional_data(self,records):
        summary_data = {}

        for record in records:
            location = record.location_id.name if record.location_id else 'N/A'
            invoice_date = record.invoice_date
            if invoice_date:
                if isinstance(invoice_date, int):
                    base_date = datetime(1899, 12, 30)
                    invoice_date = base_date + timedelta(days=invoice_date)
                date_str = invoice_date.strftime('%d-%m-%Y')
            else:
                date_str = 'N/A'

            # Initialize summary data for each location
            if location not in summary_data:
                summary_data[location] = {
                    'date': date_str,
                    'lift_off': {
                        '20 FT': 0,
                        '20 FT Reefer': 0,
                        '40 FT': 0,
                        '40 FT Reefer': 0,
                    },
                    'lift_on': {
                        '20 FT': 0,
                        '20 FT Reefer': 0,
                        '40 FT': 0,
                        '40 FT Reefer': 0,
                    },
                    'cash': 0,
                    'online': 0,
                    'total': 0,
                }

            if record.move_in_ids:
                move_in_size = self._count_container_size_movement(record.move_in_ids,
                                                                   movement_type='move_in')
                if move_in_size:
                    for container_type in ['20 FT', '20 FT Reefer', '40 FT', '40 FT Reefer']:
                        summary_data[location]['lift_off'][container_type] += move_in_size.get(
                            'lift_off', {}).get(container_type, 0)

                # Process move_out_ids
            if record.move_out_ids:
                move_out_size = self._count_container_size_movement(record.move_out_ids,
                                                                    movement_type='move_out')
                if move_out_size:
                    for container_type in ['20 FT', '20 FT Reefer', '40 FT', '40 FT Reefer']:
                        summary_data[location]['lift_on'][container_type] += move_out_size.get(
                            'lift_on', {}).get(container_type, 0)

            if record.move_in_id:
                move_in_size = self._count_container_size_movement(record.move_in_id,
                                                                   movement_type='move_in')
                if move_in_size:
                    for container_type in ['20 FT', '20 FT Reefer', '40 FT', '40 FT Reefer']:
                        summary_data[location]['lift_off'][container_type] += move_in_size.get(
                            'lift_off', {}).get(container_type, 0)

                # Process move_out_ids
            if record.move_out_id:
                move_out_size = self._count_container_size_movement(record.move_out_id,
                                                                    movement_type='move_out')
                if move_out_size:
                    for container_type in ['20 FT', '20 FT Reefer', '40 FT', '40 FT Reefer']:
                        summary_data[location]['lift_on'][container_type] += move_out_size.get(
                            'lift_on', {}).get(container_type, 0)

            # Increment payment method count and amount
            if record.payment_mode == 'cash':
                summary_data[location]['cash'] += record.total_amount  # Add total amount to Cash
            elif record.payment_mode == 'online':
                summary_data[location][
                    'online'] += record.total_amount  # Add total amount to Online

            # Total amounts
            summary_data[location]['total'] = (
                    summary_data[location]['cash'] + summary_data[location]['online']
            )

        # Format data for returning
        formatted_data = []
        for location, data in summary_data.items():
            formatted_data.append({
                'date': data['date'],
                'location': location,
                'lift_off': data['lift_off'],
                'lift_on': data['lift_on'],
                'cash': data['cash'],
                'online': data['online'],
                'total': data['total'],
            })

        return formatted_data

    def _count_container_size_movement(self, containers, movement_type):
        size_count = {
            'lift_off': {
                '20 FT': 0,
                '20 FT Reefer': 0,
                '40 FT': 0,
                '40 FT Reefer': 0,
            },
            'lift_on': {
                '20 FT': 0,
                '20 FT Reefer': 0,
                '40 FT': 0,
                '40 FT Reefer': 0,
            },
        }

        for container in containers:
            if container:
                container_size = container.type_size_id.size

                # Update size counts based on movement type
                if movement_type == 'move_in':
                    if container_size == '20FT':
                        size_count['lift_off']['20 FT'] += 1
                    elif container_size == '20FT Reefer':
                        size_count['lift_off']['20 FT Reefer'] += 1
                    elif container_size == '40FT':
                        size_count['lift_off']['40 FT'] += 1
                    elif container_size == '40FT Reefer':
                        size_count['lift_off']['40 FT Reefer'] += 1
                elif movement_type == 'move_out':
                    if container_size == '20FT':
                        size_count['lift_on']['20 FT'] += 1
                    elif container_size == '20FT Reefer':
                        size_count['lift_on']['20 FT Reefer'] += 1
                    elif container_size == '40FT':
                        size_count['lift_on']['40 FT'] += 1
                    elif container_size == '40FT Reefer':
                        size_count['lift_on']['40 FT Reefer'] += 1

        return size_count


class MoveInOutInvoiceCharge(models.Model):
    _name = "move.in.out.invoice.charge"
    _description = "Move In Out Invoice Charge"

    move_in_out_invoice_id = fields.Many2one('move.in.out.invoice', string="Invoice")
    charge_id = fields.Many2one('product.template', string="Charge",domain="[('active', '=', True)]")
    charge_name = fields.Char("Charge Name",related='charge_id.name')
    hsn_code_id = fields.Many2one("master.hsn.code", string="HSN Code" ,related='charge_id.hsn_code')
    amount = fields.Integer(string="Amount", required=True)
    qty = fields.Integer(string="Qty")
    size = fields.Char(string="Size")
    hsn_code = fields.Integer(string="HSN Code", related='hsn_code_id.code')
    total_amount = fields.Float("Total Amount", compute="_compute_totals", store=True)
    gst_breakup_cgst = fields.Float("GST Breakup (CGST)", default=0, compute='_compute_gst_amounts', store=True)
    gst_breakup_sgst = fields.Float("GST Breakup (SGST)", default=0, compute='_compute_gst_amounts', store=True)
    gst_breakup_igst = fields.Float("GST Breakup (IGST)", default=0, compute='_compute_gst_amounts', store=True)
    grand_total = fields.Float(compute="_compute_grand_totals", store=True)

    @api.depends('amount', 'qty', 'gst_breakup_cgst', 'gst_breakup_sgst', 'gst_breakup_igst')
    def _compute_totals(self):
        for record in self:
            record.total_amount = (
                    record.amount +
                    record.gst_breakup_cgst +
                    record.gst_breakup_sgst +
                    record.gst_breakup_igst)

    @api.depends('amount', 'qty', 'gst_breakup_cgst', 'gst_breakup_sgst', 'gst_breakup_igst')
    def _compute_grand_totals(self):
        # Iterate over the entire recordset to compute the grand total
        grand_total = sum(record.total_amount for record in self)
        for record in self:
            record.grand_total = grand_total

    @api.depends('charge_id', 'move_in_out_invoice_id.gst_rate', 'move_in_out_invoice_id.gst_state',
                 'move_in_out_invoice_id.location_id', 'move_in_out_invoice_id.is_gst_applicable')
    def _compute_gst_amounts(self):
        for record in self:
            cgst = sgst = igst = 0.0

            # Iterate over all GST rates
            gst_rates = record.move_in_out_invoice_id.gst_rate
            for gst in gst_rates:
                if gst:
                    tax_rate = gst
                    total_gst_rate = tax_rate.amount
                    cgst_bifurcation = sgst_bifurcation = 0.0
                    # Calculate CGST, SGST, and IGST bifurcation for each GST rate
                    for tax in gst.children_tax_ids:
                        if 'cgst' in tax.name.lower():
                            cgst_bifurcation = tax.amount
                        elif 'sgst' in tax.name.lower():
                            sgst_bifurcation = tax.amount

                    # Calculate CGST and SGST if the supply is within the same state
                    if record.move_in_out_invoice_id.gst_state == record.move_in_out_invoice_id.location_id.state_id.name:
                        cgst += (cgst_bifurcation / 100) * record.amount
                        sgst += (sgst_bifurcation / 100) * record.amount

                    # Calculate IGST if the supply is outside the state or GST is applicable
                    elif record.move_in_out_invoice_id.gst_state != record.move_in_out_invoice_id.location_id.state_id.name or record.move_in_out_invoice_id.is_gst_applicable == 'yes':
                        igst += (total_gst_rate / 100) * record.amount

            # Update the computed values
            record.gst_breakup_cgst = cgst
            record.gst_breakup_sgst = sgst
            record.gst_breakup_igst = igst
