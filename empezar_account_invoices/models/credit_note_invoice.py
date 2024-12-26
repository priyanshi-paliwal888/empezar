import base64
import json
import qrcode
import re
from datetime import date
from io import BytesIO
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.fields import Command
from odoo.addons.empezar_base.models.res_users import ResUsers
import pytz

class CreditNoteInvoice(models.Model):
    _name = "credit.note.invoice"
    _description = "Credit Note Invoice"
    _rec_name = 'credit_note_number'
    _order = "create_date desc"

    credit_note_number = fields.Char(string="Credit Note Number")
    credit_note_date = fields.Date("Credit Note Date", default=fields.Date.today)
    credit_note_invoice_id = fields.Many2one(
        comodel_name='move.in.out.invoice',
        string='Credit Note Invoice ID',
        store=True)
    invoice_reference_no = fields.Char(string="Reference Invoice No.", required=True, size=32)

    credit_note_reason = fields.Selection(
        [
            ("data_entry_issue", "Data Entry Issue"),
            ("customer_cancellation", "Customer Cancellation"),
            ("duplicate", "Duplicate"),
            ("others", "Others")
        ],
        string="Credit Note Reason")
    reason = fields.Char(string="Reason",size=64)
    invoice_number = fields.Char("Invoice No.")
    location_id = fields.Many2one('res.company', string="Location")
    currency_id = fields.Many2one("res.currency")
    invoice_date = fields.Date("Invoice Date")
    billed_to_party = fields.Many2one('res.partner', string="Billed To Party",
                                      domain="[('is_cms_parties', '=', True),('is_this_billed_to_party', '=', 'yes')]")
    charge_ids = fields.One2many('credit.note.invoice.charge','credit_note_invoice_id', String="Charges")
    billed_to_party_address = fields.Char("To Party Address")
    supply_to_state = fields.Char(string="Supply To State")
    billed_to_gst_no = fields.Many2one("gst.details", string="Billed To GST No.")
    invoice_type = fields.Selection(
        [
            ("lift_off", "Lift Off"),
            ("lift_on", "Lift On"),
            ("Others", "Others"),
        ], string="Invoice Type")
    shipping_line_id = fields.Many2one('res.partner', string="Shipping Line Id")
    shipping_line_logo = fields.Binary(string="Shipping Line")
    credit_note_details = fields.Char("Credit Note Details", compute='_compute_credit_note_details')
    party_reference_no = fields.Char("Party/Refrence No.", compute='_compute_party_reference_no', store=True)
    total_charge_amount = fields.Float(string="Total Charge Amount",
                                       compute='_compute_total_charge_amount', store=True)
    credit_note_status = fields.Selection(
        [
            ("active", "Active"),
            ("cancelled", "Cancelled"),
        ],
        string="Status", default="active"
    )
    e_invoice = fields.Selection(
        [
            ("yes", "Yes"),
            ("no", "No"),
        ],string="E Invoice")
    is_invoice_no = fields.Boolean(default=False)
    remarks = fields.Char("Remarks")
    container_no = fields.Char("Container No.")
    truck_no = fields.Char("Truck No.")
    gst_no=fields.Char("GST")
    cin_no = fields.Char("CIN")
    ack_number = fields.Char("Ack No", copy=False)
    ack_date = fields.Datetime("Ack Date", copy=False)
    cancel_irn_date = fields.Datetime("Cancel Date", copy=False)
    irn_no = fields.Char("IRN No.", copy=False)
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
    other_charge_id = fields.Many2one('product.template',
                                    string='Charge')
    amount = fields.Float("Amount", default=0)
    gst_breakup_cgst = fields.Float("GST Breakup (CGST)", default=0, compute='_compute_gst_amounts',
                                    store=True)
    gst_breakup_sgst = fields.Float("GST Breakup (SGST)", default=0, compute='_compute_gst_amounts',
                                    store=True)
    gst_breakup_igst = fields.Float("GST Breakup (IGST)", default=0, compute='_compute_gst_amounts',
                                    store=True)
    hsn_code_id = fields.Many2one('master.hsn.code', string="HSN Code")
    hsn_code = fields.Integer("HSN Code", related='hsn_code_id.code')
    gst_rate = fields.Many2many(comodel_name="account.tax", compute="_compute_gst_rate", store=True)

    @api.depends('charge_ids.gst_breakup_cgst', 'charge_ids.gst_breakup_sgst',
                 'charge_ids.gst_breakup_igst', 'charge_ids.total_amount', 'other_charge_id',
                 'amount')
    def _compute_total_charge_amount(self):
        for record in self:
            if record.invoice_type == 'Others':
                record.total_charge_amount = record.amount + record.gst_breakup_cgst + record.gst_breakup_sgst + record.gst_breakup_igst
            else:
                # Compute total of CGST, SGST, and IGST along with other charges
                record.total_charge_amount = sum(
                    charge.amount + charge.gst_breakup_cgst + charge.gst_breakup_sgst + charge.gst_breakup_igst
                    for charge in record.charge_ids)

    @api.depends('gst_rate', 'amount', 'location_id', 'supply_to_state',
                 'invoice_type', 'charge_ids')
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
                        elif record.supply_to_state != record.location_id.state_id.name:
                            igst += (total_gst_rate / 100) * amount

                # Update the computed values
                record.gst_breakup_cgst = cgst
                record.gst_breakup_sgst = sgst
                record.gst_breakup_igst = igst
            else:
                pass

    @api.depends('charge_ids.charge_id', 'invoice_type', 'location_id')
    def _compute_gst_rate(self):
        for record in self:
            if record.charge_ids and record.invoice_type != 'Others':
                for charge in record.charge_ids:
                    if charge.charge_id.gst_rate:
                        record.gst_rate = charge.charge_id.gst_rate.ids
            if record.invoice_type == 'Others' and record.other_charge_id:
                gst_rate = record.other_charge_id.gst_rate
                record.gst_rate = gst_rate

    @api.onchange('other_charge_id', 'invoice_type', 'location_id')
    def onchange_other_charge_id(self):
        for record in self:
            if record.invoice_type == 'Others' and record.other_charge_id:
                gst_rate = record.other_charge_id.gst_rate
                record.write({'gst_rate': gst_rate})

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

    def cancel_invoice_credit(self):
        """Open a wizard for canceling the invoice with the default invoice ID."""
        if self.e_invoice == 'yes':
            if not self.irn_no:
                raise ValidationError(
                    "E-Invoice has not been generated successfully. Please generate the E-Invoice first.")
        return {
            'name': 'Cancel Credit Note',
            'type': 'ir.actions.act_window',
            'res_model': 'credit.note.cancellation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_credit_id': self.id,
                'default_irn_number': self.irn_no
            }
        }

    def generate_credit_pdf(self):
        """Generate and return a PDF report for the invoice."""
        return self.env.ref(
            'empezar_account_invoices.credit_note_invoice_report_action').report_action(self)

    @api.model
    def create(self, vals):
        # res = super().create(vals)
        """Generate a credit note number based on the specified logic.
        :return: Generated credit note number
        """
        
        invoice_reference_no = vals.get('invoice_reference_no')
        credit_note_invoice = self.env['move.in.out.invoice'].search(
                [('invoice_number', '=', invoice_reference_no)], limit=1)
        vals["credit_note_date"] = date.today()
        location_id = credit_note_invoice.location_id
        vals["location_id"] = credit_note_invoice.location_id.id
        if location_id:
            location_code = location_id.location_code
            fiscal_year = 2324

            sequence = self.env['ir.sequence'].next_by_code('credit.note.invoice') or _("New")
            fixed_text = "CRN"
            credit_note_number = f"{fixed_text}{location_code}{fiscal_year}{sequence}"
            vals['credit_note_number'] = credit_note_number
        return super().create(vals)

    def write(self, vals):
        credit_month = self.credit_note_date.month
        fiscal_year_id = self.env['account.fiscal.year'].search([('date_from', '<=', self.credit_note_date), ('date_to', '>=', self.credit_note_date)], limit=1)
        location = self.env['monthly.lock'].search([
            ('fiscal_year', '=', fiscal_year_id.id),
            ('location_id', '=', self.location_id.name),
            ('month', '=', credit_month),
            ('invoice_type', '=', "credit")
        ], limit=1)

        if location and location.is_locked:
            raise ValidationError(
                "Credit Note cannot be created as credit note creation is already locked. Please contact system admin for further support.")

        return super().write(vals)

    @api.depends('credit_note_number', 'credit_note_date')
    def _compute_credit_note_details(self):
        for record in self:
            record.credit_note_details = False
            if record.credit_note_date:
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
                formatted_credit_note_date = record.credit_note_date.strftime(
                date_formats.get(company_format, '%d/%m/%Y'))
            
            if record.credit_note_number and record.credit_note_date :
                record.credit_note_details = f"{record.credit_note_number} {formatted_credit_note_date}"

    @api.depends('billed_to_party', 'invoice_number')
    def _compute_party_reference_no(self):
        for record in self:
            record.party_reference_no = False
            if record.billed_to_party and record.invoice_number:
                record.party_reference_no = f"{record.billed_to_party.name} {record.invoice_number}"

    def _get_report_filename(self):
        """Generate the filename for the credit note report based on Move In or Move Out details."""
        credit_note_invoice = self.env['move.in.out.invoice'].search(
                [('invoice_number', '=', self.invoice_reference_no)], limit=1)
        if credit_note_invoice.move_in_id:
            container_no = credit_note_invoice.move_in_id.container if credit_note_invoice.move_in_id.container else ''
            credit_note_number = self.credit_note_number or ''
            move_date = credit_note_invoice.move_in_id.move_in_date_time.strftime('%d-%m-%Y') if credit_note_invoice.move_in_id.move_in_date_time else ''
            name = f"{container_no}_{credit_note_number}_{move_date}"
        elif credit_note_invoice.move_out_id:
            container_no = credit_note_invoice.move_out_id.container_id.name if credit_note_invoice.move_out_id.container_id.name else ''
            credit_note_number = self.credit_note_number or ''
            move_date = credit_note_invoice.move_out_id.move_out_date_time.strftime('%d-%m-%Y') if credit_note_invoice.move_out_id.move_out_date_time else ''
            name =  f"{container_no}_{credit_note_number}_{move_date}"
        else:
            name = self.credit_note_number or ''
        return name

    @api.onchange('charge_ids.amount')
    def _check_amount(self):
        for rec in self.charge_ids:
            if rec.amount < 0:
                raise ValidationError(_("Amount cannot be a negative value"))

    @api.depends('amount')
    @api.constrains('charge_ids.amount', 'invoice_reference_no','amount','charge_ids.charge_id')
    def _check_invoice_no(self):
        """Check if the invoice number is already present in the system."""
        if self.invoice_reference_no:
            # Search for the invoice in 'move.in.out.invoice' model
            credit_note_invoice = self.env['move.in.out.invoice'].search(
                [('invoice_number', '=', self.invoice_reference_no)], limit=1)
            if credit_note_invoice.invoice_type != 'Others':
                for charge in credit_note_invoice.charge_ids:
                    if charge.charge_id.active == False:
                        raise ValidationError(_("Charge must be active"))
            if credit_note_invoice.invoice_type == 'Others':
                if credit_note_invoice.other_charge_id.active == False:
                    raise ValidationError(_("Charge must be active"))
            if credit_note_invoice.billed_to_party.active == False:
                raise ValidationError(_("The billed-to party is disabled."))
            if credit_note_invoice.invoice_status == 'cancelled':
                raise ValidationError(_('Please select active invoice number.'))
            elif credit_note_invoice.invoice_status == 'active':
                pass
            else:
                raise ValidationError(_("Invoice Number not found"))

            total = 0
            original_invoice_amount = 0
            if credit_note_invoice.invoice_type != 'Others':
                credit_note_invoice_amount = self.env['credit.note.invoice'].search([('invoice_reference_no','=', self.invoice_reference_no),('id','!=',self.id),('credit_note_status','=','active')]).mapped('charge_ids')
                for charge in credit_note_invoice_amount:
                    total += charge.amount
                for charge in credit_note_invoice.charge_ids:
                    original_invoice_amount += charge.amount
                # original_invoice_amount = credit_note_invoice.charge_ids.amount
                remaining_amount = original_invoice_amount - total
                if remaining_amount <= 0:
                    raise ValidationError(_("Cannot create credit note. The amount will exceeds the available balance for the invoice."))
            else:
                credit_note_invoice_amount = self.env['credit.note.invoice'].search([('invoice_reference_no','=', self.invoice_reference_no),('id','!=',self.id),('credit_note_status','=','active')]).mapped('amount')
                total = sum(credit_note_invoice_amount)
                original_invoice_amount = credit_note_invoice.amount
                remaining_amount = original_invoice_amount -total
                if remaining_amount <= 0:
                    raise ValidationError(_("Cannot create credit note.The amount will exceeds the available balance for the invoice."))
                if self.id:
                    if self.amount > remaining_amount:
                        raise ValidationError(_("Cannot create credit note.The amount will exceeds the available balance for the invoice."))
            fiscal_year_id = self.env['account.fiscal.year'].search([('date_from', '<=', self.credit_note_date),('date_to', '>=', self.credit_note_date)], limit=1)
            credit_month = self.credit_note_date.month
            location = self.env['monthly.lock'].search([
                ('fiscal_year','=',fiscal_year_id.id),
                ('location_id', '=', self.location_id.id),
                ('month', '=', credit_month),
                ('invoice_type', '=', "credit")
            ], limit=1)

            if location and location.is_locked:
                raise ValidationError(
                    "Credit Note cannot be created as credit note creation is already locked. Please contact system admin for further support.")

    def action_check_invoice_no(self):
        """Check if the invoice number is already present in the system."""
        if self.invoice_reference_no:
            # Search for the invoice in 'move.in.out.invoice' model
            credit_note_invoice = self.env['move.in.out.invoice'].search(
                [('invoice_number', '=', self.invoice_reference_no)], limit=1)
            
            try:
                if credit_note_invoice.e_invoice == 'yes':
                    self.e_invoice_integration(self.credit_note_number)
            except Exception as e:
                # Handle any exception during IRN generation
                print(f"Error generating IRN: {e}")

            if credit_note_invoice.invoice_status == 'cancelled':
                raise ValidationError(_('Please select active invoice number.'))

            credit_note_invoices_amount = self.env['credit.note.invoice'].search([
                ('invoice_reference_no', '=', self.invoice_reference_no),
                ('id', '!=', self.id), ('credit_note_status','=','active')
            ])
            # Assign values from the found invoice to the current record
            self.invoice_number = credit_note_invoice.invoice_number
            self.invoice_date = credit_note_invoice.invoice_date
            self.invoice_type = credit_note_invoice.invoice_type
            self.billed_to_gst_no = credit_note_invoice.billed_to_gst_no
            self.supply_to_state = credit_note_invoice.supply_to_state
            self.billed_to_party_address = credit_note_invoice.billed_to_party_address
            self.location_id = credit_note_invoice.location_id.id
            self.currency_id = credit_note_invoice.currency_id.id
            self.billed_to_party = credit_note_invoice.billed_to_party.id
            self.shipping_line_id = credit_note_invoice.shipping_line_id.id
            self.shipping_line_logo = credit_note_invoice.shipping_line_logo
            self.total_charge_amount = credit_note_invoice.total_charge_amount
            self.e_invoice = credit_note_invoice.e_invoice
            self.remarks = credit_note_invoice.remarks
            self.is_invoice_no = True
            if self.invoice_type == 'Others':
                total_credit_note = 0
                for credit_note in credit_note_invoices_amount:
                    total_credit_note += credit_note.amount
                original_invoice_amount = credit_note_invoice.amount
                remaining_amount = original_invoice_amount - total_credit_note
                self.other_charge_id = credit_note_invoice.other_charge_id.id
                self.amount = min(credit_note_invoice.amount,remaining_amount)
                self.gst_breakup_cgst = credit_note_invoice.gst_breakup_cgst
                self.gst_breakup_sgst = credit_note_invoice.gst_breakup_sgst
                self.gst_breakup_igst = credit_note_invoice.gst_breakup_igst
                self.hsn_code_id = credit_note_invoice.hsn_code_id.id
                self.hsn_code = credit_note_invoice.hsn_code_id.code

            else:
                self.charge_ids = [
                        Command.create({
                            'charge_id': charge.charge_id.id,
                            'amount': 0,
                            'qty': charge.qty,
                            'total_amount': charge.total_amount,
                            'gst_breakup_cgst': charge.gst_breakup_cgst,
                            'gst_breakup_sgst': charge.gst_breakup_sgst,
                            'gst_breakup_igst': charge.gst_breakup_igst,
                            'grand_total': charge.grand_total,
                            'size': charge.size,
                            'hsn_code_id': charge.hsn_code_id.id,
                        }) for  charge in credit_note_invoice.charge_ids
                    ]
            if credit_note_invoice.move_in_id:
                self.container_no = credit_note_invoice.move_in_id.container
                self.truck_no = credit_note_invoice.move_in_id.truck_no
                invoice_shipping_line = credit_note_invoice.move_in_id.location_id.invoice_setting_ids
                for shipping_line in invoice_shipping_line:
                    if self.shipping_line_id.id == shipping_line.inv_shipping_line_id.id:
                        self.gst_no = shipping_line.gst_number
                        self.cin_no = shipping_line.cin_no
            if credit_note_invoice.move_out_id:
                self.container_no = credit_note_invoice.move_out_id.inventory_id.name
                self.truck_no = credit_note_invoice.move_out_id.truck_number
                invoice_shipping_line = credit_note_invoice.move_out_id.location_id.invoice_setting_ids
                for shipping_line in invoice_shipping_line:
                    if self.shipping_line_id.id == shipping_line.inv_shipping_line_id.id:
                        self.gst_no = shipping_line.gst_number
                        self.cin_no = shipping_line.cin_no


    @api.depends('charge_ids.total_amount')
    def compute_total_charge_amount(self):
        """Method to compute the total amount."""
        for rec in self:
            if rec.invoice_type == "Others":
                rec.total_charge_amount = rec.amount
            else:
                rec.total_charge_amount = sum(rec.charge_ids.mapped('total_amount'))


    def e_invoice_integration(self,credit_note_number):
        invoice_ref_number = self.env['move.in.out.invoice'].search([('invoice_number','=',self.invoice_reference_no)])
        irn_data = self.prepare_generate_irn(location=invoice_ref_number.location_id, charges=invoice_ref_number.charge_ids.ids, shipping_line_id=invoice_ref_number.shipping_line_id.id, billed_party=invoice_ref_number.billed_to_party,
                             invoice_number=invoice_ref_number.invoice_number, billed_to_gst_no=invoice_ref_number.billed_to_gst_no,invoice_date=invoice_ref_number.invoice_date, credit_note_number= credit_note_number)
        try:
            try:
                api_response = invoice_ref_number.authenticate_einvoice_api()

                # Check if the authentication response is successful
                if api_response and api_response['status_cd'] == 'Sucess':
                    auth_token = api_response['data'].get('AuthToken')
                    invoice_ref_number.auth_token = auth_token
                else:
                    error_messages = json.loads(api_response['status_desc'])

                    # Prepare a structured output
                    errors = []
                    for error in error_messages:
                        errors.append(
                            f"ErrorMessage: {error['ErrorMessage']}")

                    # Join all error messages into a single string or store them in a field
                    all_errors = "\n".join(errors)
                    self.response_error = all_errors
            except Exception as e:
                # Handle any exception during IRN generation
                print(f"Error generating IRN: {e}")

            try:
                # Generate IRN (Invoice Reference Number)
                irn_data = invoice_ref_number.generate_irn(auth_token, body_data=irn_data)
                if irn_data and irn_data['status_cd'] == '1':
                    self.ack_date = irn_data['data'].get('AckDt')
                    self.ack_number = irn_data['data'].get('AckNo')
                    self.irn_no = irn_data['data'].get('Irn')
                    self.jwt_string = irn_data['data'].get('SignedQRCode')
                    generate_irn_response = json.dumps(irn_data, indent=4)
                    self.generate_irn_response = generate_irn_response
                    self.is_success = True
                else:
                    error_messages = json.loads(irn_data['status_desc'])

                    # Prepare a structured output
                    errors = []
                    for error in error_messages:
                        errors.append(
                            f"ErrorMessage: {error['ErrorMessage']}")

                    # Join all error messages into a single string or store them in a field
                    all_errors = "\n".join(errors)
                    self.response_error = all_errors

            except Exception as e:
                # Handle any exception during IRN generation
                print(f"Error generating IRN: {e}")
        except KeyError as e:
            # Handle missing keys in the response
            print(f"Error generating IRN: {e}")

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

    def prepare_generate_irn(self, location, charges, shipping_line_id, billed_party,
                             invoice_number, billed_to_gst_no, invoice_date,credit_note_number):
        ItemList = []
        location_id = self.env['res.company'].search([('id', '=', location.id)], limit=1)
        billed_to_party = self.env['res.partner'].search([('id', '=', billed_party.id)], limit=1)
        billed_to_gst_no_id = self.env['gst.details'].search([('id', '=', billed_to_gst_no.id)],
                                                             limit=1)

        current_date = date.today()
        formatted_credit_note_date = current_date.strftime("%d/%m/%Y")
        formated_invoice_date = invoice_date.strftime("%d/%m/%Y")

        if billed_to_gst_no_id and billed_to_gst_no_id.nature_of_business == 'Special Economic Zone' and billed_to_gst_no_id.gst_rate:
            sub_type = 'SEZWP'
        elif billed_to_gst_no_id and billed_to_gst_no_id.nature_of_business == 'Special Economic Zone' and not billed_to_gst_no_id.gst_rate:
            sub_type = 'SEZWOP'
        else:
            sub_type = 'B2B'

        if location_id and shipping_line_id:
            matching_setting = location_id.invoice_setting_ids.filtered(
                lambda setting: setting.inv_shipping_line_id.id == shipping_line_id
            )
            lgname = f'{matching_setting.inv_applicable_at_location_ids.mapped("name")}{matching_setting.inv_shipping_line_id.name}'

        ValDtls = {
            "AssVal": 0,
            "CgstVal": 0,
            "SgstVal": 0,
            "IgstVal": 0,
            "TotInvVal": 0,
        }
        charge_ids = self.env['move.in.out.invoice.charge'].search([('id', 'in', charges)])
        for index, charge in enumerate(charge_ids, start=1):
            gst_rate = self.calculate_gst_rate_value(charge,{'invoice_type':self.invoice_type,'other_charge_id':charge.charge_id.id})

            taxable_value = charge.total_amount - (
                    charge.gst_breakup_cgst + charge.gst_breakup_sgst + charge.gst_breakup_igst)

            # Calculate IGST using the taxable value and GST rate from the charge
            igst_amount = round(taxable_value * (gst_rate/ 100)) if charge is not None else 0.00

            ItemList.append({
                "SlNo": str(index),
                "PrdDesc": charge.charge_name,
                "IsServc": "Y",
                "HsnCd": str(charge.charge_id.hsn_code.code),
                "UnitPrice": charge.amount,
                "TotAmt": charge.total_amount,
                "AssAmt": charge.total_amount,
                "GstRt":  gst_rate,
                "IgstAmt": igst_amount,
                "CgstAmt": charge.gst_breakup_cgst,
                "SgstAmt": charge.gst_breakup_sgst,
                "TotItemVal": charge.total_amount + igst_amount + charge.gst_breakup_cgst + charge.gst_breakup_sgst,
            })

            ValDtls["AssVal"] += charge.total_amount
            ValDtls["CgstVal"] += charge.gst_breakup_cgst
            ValDtls["SgstVal"] += charge.gst_breakup_sgst
            ValDtls["IgstVal"] += igst_amount
            ValDtls[
                "TotInvVal"] += charge.total_amount + igst_amount + charge.gst_breakup_cgst + charge.gst_breakup_sgst
        for key, val in ValDtls.items():
            ValDtls[key] = round(ValDtls[key], 2)
        param = {
            "Version": "1.1",
            "TranDtls": {
                "TaxSch": "GST",
                "SupTyp": sub_type,
            },
            "DocDtls": {
                "Typ": "CRN",
                "No": credit_note_number,
                "Dt": formatted_credit_note_date,
            },
            "SellerDtls": {
                "Gstin": matching_setting.gst_number,
                "LglNm": lgname,
                "Addr1": matching_setting.address_line_1,
                "Addr2": matching_setting.address_line_2,
                "Loc": matching_setting.city,
                "Pin": matching_setting.pincode,
                "Stcd": "29",  # state code with come here numberic code
            },
            "BuyerDtls": {
                "Gstin":  "29AWGPV7107B1Z1",#billed_to_gst_no_id.gst_no,
                "LglNm": billed_to_party.party_name,
                "Addr1": billed_to_party.street,
                "Addr2": billed_to_party.street2,
                "Pos": "12",  # invoice supply to state code will come here
                "Loc": billed_to_party.gst_state,
                "Pin": billed_to_party.zip,
                "Stcd": "29",  # state code will come here
            },
            "ItemList": ItemList,
            "ValDtls": ValDtls,
            "PrecDocDtls": {
                "InvNo": invoice_number,
                "InvDt":formated_invoice_date,
            },
        }

        return param

    def refresh_invoice(self):
        self.e_invoice_integration(self.credit_note_number)

    def e_invoice_credit_record(self):

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
            'name': f'E-Invoice - {self.credit_note_number} ',
            'type': 'ir.actions.act_window',
            'res_model': 'e.invoice.credit.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_credit_id': self.id,
                'default_invoice_ref_no': self.invoice_reference_no,
                'default_irn_no': self.irn_no,
                'default_irn_received_date': self.ack_date,
                'default_irn_status': self.irn_status,
                'default_generate_irn_response': self.generate_irn_response,
                'default_irn_date': formatted_date_time,
            }
        }

    def show_error(self):
        return {
            'type': 'ir.actions.act_window',
            'name': f'ERROR - {self.credit_note_number}',
            'res_model': 'credit.note.invoice',
            'view_mode': 'form',
            'views': [(self.env.ref('empezar_account_invoices.error_credit_response_view').id, 'form')],
            'res_id': self.id,
            'target': 'new',
        }
    def e_invoice_view(self):
        """Open a form for viewing the E-Invoice with the default invoice ID."""
        for record in self:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            if record.invoice_reference_no:
                # Ensure the credit note invoice exists
                credit_note_invoice = self.env['move.in.out.invoice'].search(
                    [('invoice_number', '=', record.invoice_reference_no)], limit=1)
                if credit_note_invoice:
                    action_id = self.env.ref('empezar_account_invoices.invoices_action').id  # Action ID for move.in form view
                    menu_id = self.env.ref('empezar_account_invoices.menu_invoices').id  # Menu ID for move.in

                    invoice_url = f"{base_url}/web#id={credit_note_invoice.id}&model=move.in.out.invoice&view_type=form&menu_id={menu_id}&action={action_id}"

                    return {
                        'type': 'ir.actions.act_url',
                        'url': invoice_url,
                        'target': 'new',
                    }
                else:
                    raise UserError(_("The specified invoice could not be found. Please verify the invoice reference number."))
            else:
                raise UserError(_("Invoice reference number is missing."))

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
