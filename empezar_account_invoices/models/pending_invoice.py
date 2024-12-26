""" -*- coding: utf-8 -*- """
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from .helper import e_invoice_integration
from odoo.addons.empezar_base.models.res_users import ResUsers


class PendingInvoices(models.Model):
    _name = "pending.invoices"
    _description = "Pending Invoices"
    _rec_name = "movement_type"
    _order = "create_date desc"

    movement_type = fields.Selection([
        ('move_in', 'Move In'),
        ('move_out', 'Move Out')
    ], string="Movement Type")

    move_in_id = fields.Many2one('move.in', string="Move In Record")
    move_out_id = fields.Many2one('move.out', string="Move Out Record")

    shipping_line_logo = fields.Binary(
        string="Shipping Line", related="shipping_line_id.logo")
    shipping_line_id = fields.Many2one(
        "res.partner",
        string="Shipping Line", domain="[('is_shipping_line', '=', True)]")
    active = fields.Boolean(string="Active", default=True)
    location_id = fields.Many2one('res.company',
                                  string="Location",
                                  default=lambda self: self.env.user.company_id)
    billed_to_party = fields.Many2one('res.partner', string="Billed To Party",
                                      domain="[('is_cms_parties', '=', True),"
                                             "('is_this_billed_to_party', '=', 'yes')]")
    container_number = fields.Char(string="Container Number")
    container_details = fields.Char("Container Details")
    movement_date_time = fields.Datetime(string="Movement Date Range")
    booking_no_id = fields.Many2one('vessel.booking', string="Booking No.")
    invoice_date = fields.Date(string="Invoice Date", default=fields.Date.context_today)
    due_date = fields.Date(string="Due Date")
    gst_details_id = fields.Many2one('gst.details', string="Billed To GST No.",
                                     domain="[('partner_id', '=', billed_to_party)]")
    billed_to_party_address = fields.Char("Billed To Party Address", compute='_compute_billed_to_party_address', store=True , readonly=False)
    currency_id = fields.Many2one("res.currency",related='location_id.currency_id')
    gst_rate = fields.Many2many(comodel_name="account.tax",
                                relation="product_taxes_rel",
                                column1="prod_id",
                                column2="tax_id",
                                help="Default taxes used when selling the product.",
                                string="GST Rate",
                                domain=[("type_tax_use", "=", "sale"), ("active", "=", True)],
                                related='charge_ids.charge_id.gst_rate')
    gst_rate_display = fields.Float()
    is_gst_applicable = fields.Selection(
        [
            ("yes", "Yes"),
            ("no", "No"),
        ], string="GST Applicable", required=True, default="yes")
    remarks = fields.Char("Remarks", compute='_compute_remarks_display', store=True, readonly=False, size=100)
    selected_record_ids = fields.Many2many(
        'pending.invoices',
        'pending_invoices_selected_rel',
        'src_invoice_id',
        'dest_invoice_id',
        string="Selected Records")
    is_invoice_setting = fields.Boolean(string="Is Invoice Setting",
                                        compute="_compute_is_invoice_setting",
                                        store=True,
                                        default=False)
    invoice_type = fields.Selection([
        ('lift_off', 'Lift Off'),
        ('lift_on', 'Lift On')
    ], string='Invoice Type')
    charge_ids = fields.One2many('pending.invoice.charge', 'invoice_id', string="Charges", compute='_compute_selected_record_ids', store=True)
    invoice_number = fields.Char("Invoice Number")
    total_amount = fields.Float(string="Total Amount", compute='_compute_total_amount', store=True)
    is_sez = fields.Boolean(string="Is SEZ", compute='_compute_billed_to_gst_no')
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
    display_create_info = fields.Char(compute="_get_create_record_info")
    display_modified_info = fields.Char(compute="_get_modify_record_info")
    display_sources = fields.Char(string="Source", readonly=True, default="Web")

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


    @api.depends("billed_to_party.street", "billed_to_party.street2")
    def _compute_billed_to_party_address(self):
        for record in self:
            record.billed_to_party_address = ''
            if record.billed_to_party.street or record.billed_to_party.street2:
                record.billed_to_party_address = f"{record.billed_to_party.street} {record.billed_to_party.street2}"

    @api.depends('billed_to_party.parties_gst_invoice_line_ids')
    def _compute_is_parties_gst_invoice_line_empty(self):
        """Condition to check the GST lines present or not in parties"""
        for record in self:
            # Check if `parties_gst_invoice_line_ids` is empty
            record.is_parties_gst_invoice_line_empty = not bool(
                record.billed_to_party.parties_gst_invoice_line_ids)

    @api.depends('gst_details_id')
    def _compute_billed_to_gst_no(self):
        """set the GST related field values"""
        for record in self:
            if record.gst_details_id:
                record.tax_payer_type = record.gst_details_id.tax_payer_type
                record.state_jurisdiction = record.gst_details_id.state_jurisdiction
                record.company_id = record.gst_details_id.company_id
                record.nature_of_business = record.gst_details_id.nature_of_business
                record.place_of_business = record.gst_details_id.place_of_business
                record.additional_place_of_business = record.gst_details_id.additional_place_of_business
                record.nature_additional_place_of_business = record.gst_details_id.nature_additional_place_of_business
                record.additional_place_of_business_2 = record.gst_details_id.additional_place_of_business_2
                record.nature_additional_place_of_business_2 = record.gst_details_id.nature_additional_place_of_business_2
                record.last_update = record.gst_details_id.last_update
                record.gst_api_response = record.gst_details_id.gst_api_response
                record.gst_state = record.billed_to_party.gst_state

            if record.gst_details_id and record.gst_details_id.nature_of_business == 'Special Economic Zone':
                record.is_sez = True
            else:
                record.is_sez = False

    @api.depends('charge_ids.total_amount')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = sum(charge.total_amount for charge in record.charge_ids)

    @api.depends('selected_record_ids', 'movement_type')
    def _compute_selected_record_ids(self):
        """ Compute the selected record ids"""

        # Clear existing charge records
        self.charge_ids = [(5, 0, 0)]
        unique_charges = {}

        if self.selected_record_ids:
            for record in self.selected_record_ids:
                # Ensure movement_type exists
                if not hasattr(record, 'movement_type'):
                    continue

                movement_type = record.movement_type
                container_type = record.move_in_id.type_size_id if record.move_in_id else record.move_out_id.type_size_id

                if container_type:
                    size = "20 FT" if container_type.te_us == 1 else "40 FT"

                    # Fetch active charge records based on movement type
                    charges = self.env['product.template'].search([
                        ('invoice_type', '=', record.invoice_type),
                        ('active', '=', True),
                    ])

                    for charge in charges:
                        key = (movement_type, container_type.size)  # Unique key for charge and size
                        if key not in unique_charges:
                            # Call set_amount to get the correct amount
                            location_id = record.location_id  # Ensure location_id is available
                            invoice_type = record.invoice_type  # Extract invoice type
                            move_in_id = record.move_in_id
                            move_out_id = record.move_out_id

                            amount = self.set_amount(location_id, invoice_type, move_in_id, move_out_id)

                            unique_charges[key] = {
                                'charge_id': charge.id,
                                'size': size,
                                'hsn_code': charge.hsn_code,
                                'amount': amount if amount is not None else 0,
                                'qty': 0
                            }
                        unique_charges[key]['qty'] += 1

            charge_records = []
            for charge in unique_charges.values():
                total_amount =  float(charge['amount']) * charge['qty']
                charge_records.append((0, 0, {
                    'charge_id': charge['charge_id'],
                    'hsn_code': charge['hsn_code'].code,
                    'amount': charge['amount'],
                    'qty': charge['qty'],
                    'size': charge['size'],
                    'total_amount': total_amount,
                }))
            self.charge_ids = charge_records

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

    @api.depends('location_id', 'shipping_line_id')
    def _compute_is_invoice_setting(self):
        """
        Compute the invoice setting based on location and shipping line.
        """
        for record in self:
            record.is_invoice_setting = False
            if record.location_id and record.shipping_line_id:
                # Ensure the related model 'invoice_setting_ids' and 'inv_shipping_line_id' are correctly referenced
                mapped_lines = record.location_id.invoice_setting_ids.filtered(
                    lambda line: line.inv_shipping_line_id == record.shipping_line_id
                )
                if mapped_lines:
                    record.is_invoice_setting = True

    @api.onchange('billed_to_party')
    def onchange_billed_to_party(self):
        """Updates 'billed_to_gst_no' based on the selected 'billed_to_party'
           by searching for related GST records."""
        if self.billed_to_party:
            gst_records = self.env['gst.details'].search(
                [('partner_id', '=', self.billed_to_party.id)])
            if len(gst_records) == 1:
                self.gst_details_id = gst_records[0]
            else:
                self.gst_details_id = False

    @api.model
    def default_get(self, fields):
        """ Override the default get method to set the selected record ids"""
        res = super().default_get(fields)
        # Get the selected record IDs from the context
        selected_records = self.env.context.get('default_selected_record_ids', [])
        if selected_records:
            pending_invoice = self.env['pending.invoices'].search([('id','in',selected_records)])
            res.update({
                'selected_record_ids': [(6, 0, selected_records)],
                'billed_to_party':pending_invoice.billed_to_party.id
            })
        return res

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
                        "EXPORT UNDER LUT BOND. ARN NO. "
                        "DATED:  (IGST @ IGST AMOUNT: ) "
                        "SUPPLY MEANT FOR EXPORT UNDER LETTER OF UNDERTAKING WITHOUT PAYMENT OF GST"
                    )
                else:
                    pass

    @api.constrains('due_date', 'invoice_date')
    def _check_due_date(self):
        """Ensure Due Date is not before Invoice Date."""
        for record in self:
            if record.due_date and record.due_date < record.invoice_date:
                raise ValidationError(_("Due Date cannot be earlier than the Invoice Date."))

    def update_billed_party(self, billed_party, vals, gst_no):
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

    def _validate_parties_gst_number(self, gst_no, partner_id=None):
        if len(gst_no) != 15:
            raise ValidationError("GST Number entered should be 15 characters long. Please enter the correct GST Number.")
        if not gst_no.isalnum():
            raise ValidationError("Please enter an alphanumeric GST Number.")
        if partner_id:
            existing_gst_nos = self.env['gst.details'].search(
                [("partner_id", "!=", False),('partner_id','!=',partner_id.id)]).mapped("gst_no")

            if gst_no in existing_gst_nos:
                raise ValidationError(
                    " GST Number is already set Please enter a different GST Number.")

        return {"success": "true"}

    @api.model
    def create(self, vals):
        """Call super to create the invoice"""
        invoice = super().create(vals)
        # Retrieve all selected record IDs from the context
        selected_record_ids = self.env.context.get('default_selected_record_ids', [])

        if selected_record_ids:
            fixed_text = "INV"
            # Use the first selected record to derive location information
            first_selected_record = self.env['pending.invoices'].browse(selected_record_ids[0])
            location_id = first_selected_record.location_id
            shipping_line_id = first_selected_record.shipping_line_id
            location_code = location_id.location_code if location_id else ""
            fiscal_year = 2324
            sequence = self.env['ir.sequence'].next_by_code('move.in.out.invoice') or _("New")
            invoice_number = f"{fixed_text}{location_code}{fiscal_year}{sequence}"

            # Initialize sets to collect distinct invoice types and lists for IDs
            invoice_type_labels = set()
            move_in_ids = []
            move_out_ids = []

            gst_no = vals.get('gst_no')
            if gst_no:
                if first_selected_record.billed_to_party:
                    self.update_billed_party(first_selected_record.billed_to_party, vals, gst_no)
                    self._validate_parties_gst_number(gst_no,first_selected_record.billed_to_party)

            # Loop through all selected records to gather information
            selected_records = self.env['pending.invoices'].browse(selected_record_ids)
            for selected_record in selected_records:
                # if selected_record.move_in_id:
                #     move_in_ids.append(selected_record.move_in_id.id)
                # if selected_record.move_out_id:
                #     move_out_ids.append(selected_record.move_out_id.id)

                # Collect the invoice type from each selected record
                if selected_record.invoice_type:
                    invoice_type_selection = dict(
                        self.fields_get(allfields=['invoice_type'])['invoice_type']['selection'])
                    invoice_type_labels.add(
                        invoice_type_selection.get(selected_record.invoice_type))

            # Prepare the invoice types string
            invoice_types_str = ', '.join(sorted(invoice_type_labels))
            if location_id and shipping_line_id:
                matching_setting = location_id.invoice_setting_ids.filtered(
                    lambda setting: setting.inv_shipping_line_id.id == shipping_line_id.id
                )
                if matching_setting:
                    # Safely access the first match to set the e_invoice value
                    e_invoice = matching_setting[0].e_invoice_applicable
                else:
                    e_invoice = False  # Default to False if no match is found
            else:
                e_invoice = False  # Default to False if no location or shipping line

            # Prepare the values for the move.in.out.invoice
            invoice_vals = {
                'invoice_number': invoice_number,
                'billed_to_gst_no': vals.get('gst_details_id') or first_selected_record.move_in_id.billed_to_party.parties_gst_invoice_line_ids.id,
                'is_gst_applicable': vals.get('is_gst_applicable'),
                'remarks': vals.get('remarks'),
                'payment_mode': 'cash',
                'source': "account",
                'shipping_line_id': first_selected_record.shipping_line_id.id,
                'billed_to_party': first_selected_record.billed_to_party.id,
                'location_id': first_selected_record.location_id.id,
                'invoice_types': invoice_types_str,
                'e_invoice': e_invoice,
            }
            # Create the move.in.out.invoice
            move_in_out_invoice = self.env['move.in.out.invoice'].with_context({'from_pending_invoice': True}).create(invoice_vals)
            charge_vals = vals.get('charge_ids')
            if not charge_vals:
                raise ValidationError( f"Charge must be present and it should be active")

            charge_records = []
            for charge_data in charge_vals:
                charge_id = charge_data[2].get('charge_id')
                amount = charge_data[2].get('amount')

                # Fetch the charge record to check its active status
                charge_record = self.env['product.template'].browse(charge_id)
                # Validate that the charge is active
                if not charge_record.active:
                    raise ValidationError(
                        f"The charge {charge_record.name} is not active. Please select an active charge.")

                # Validate that the amount is present and greater than zero
                if not amount or amount <= 0:
                    raise ValidationError(
                        f"The charge {charge_record.name} must have a valid amount greater than zero.")

            # Collect charge ids from the selected records and format for many2many assignment
            for charge_data in charge_vals:
                charge_record = {
                    'charge_id': charge_data[2].get('charge_id'),
                    'size': charge_data[2].get('size'),
                    'amount': charge_data[2].get('amount'),
                    'qty': charge_data[2].get('qty'),
                    'gst_breakup_igst': charge_data[2].get('gst_breakup_igst'),
                    'gst_breakup_cgst': charge_data[2].get('gst_breakup_cgst'),
                    'gst_breakup_sgst': charge_data[2].get('gst_breakup_sgst'),
                    'total_amount': charge_data[2].get('total_amount'),
                    'move_in_out_invoice_id': move_in_out_invoice.id
                }
                charge_records.append((0, 0, charge_record))

            move_in_out_invoice.charge_ids = charge_records
            e_invoice_integration(move_in_out_invoice)
            for selected_record in selected_records:
                if selected_record.move_in_id:
                    move_in_ids.append(selected_record.move_in_id.id)
                    selected_record.move_in_id.is_invoice_created = True
                if selected_record.move_out_id:
                    move_out_ids.append(selected_record.move_out_id.id)
                    selected_record.move_out_id.is_invoice_created = True
            move_in_out_invoice.write({
                'move_in_ids': [(6, 0, move_in_ids)],
                'move_out_ids': [(6, 0, move_out_ids)],
            })

        return invoice

    def action_view_move_in_out_records(self):
        """ Set the URL for the redirect to the move in move out records"""
        for record in self:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            if record.move_in_id:
                # Replace with actual action and menu IDs
                action_id = self.env.ref('empezar_move_in.move_in_action').id  # Action ID for move.in form view
                menu_id = self.env.ref('empezar_move_in.menu_move_in').id  # Menu ID for move.in

                move_in_url = f"{base_url}/web#id={record.move_in_id.id}&model=move.in&view_type=form&menu_id={menu_id}&action={action_id}"

                return {
                    'type': 'ir.actions.act_url',
                    'url': move_in_url,
                    'target': 'new',  # This opens in a new tab
                }
            if record.move_out_id:
                # Replace with actual action and menu IDs
                action_id = self.env.ref('empezar_move_out.move_out_action').id
                menu_id = self.env.ref('empezar_move_out.menu_move_out').id

                move_out_url = f"{base_url}/web#id={record.move_out_id.id}&model=move.out&view_type=form&menu_id={menu_id}&action={action_id}"

                return {
                    'type': 'ir.actions.act_url',
                    'url': move_out_url,
                    'target': 'new',  # This opens in a new tab
                }


class PendingInvoiceCharge(models.Model):
    _name = "pending.invoice.charge"
    _description = "Pending Invoice Charge"

    invoice_id = fields.Many2one('pending.invoices', string="Invoice")
    charge_id = fields.Many2one('product.template', string="Charge")
    charge_name = fields.Char("Charge Name",related='charge_id.name')
    hsn_code_id = fields.Many2one("master.hsn.code", string="HSN Code" ,related='charge_id.hsn_code')
    amount = fields.Integer(string="Amount")
    qty = fields.Integer(string="Qty")
    size = fields.Char(string="Size")
    total_amount = fields.Float("Total Amount", compute="_compute_totals")
    gst_breakup_cgst = fields.Float("GST Breakup (CGST)", default=0, compute='_compute_gst_amounts')
    gst_breakup_sgst = fields.Float("GST Breakup (SGST)", default=0, compute='_compute_gst_amounts')
    gst_breakup_igst = fields.Float("GST Breakup (IGST)", default=0, compute='_compute_gst_amounts')
    grand_total = fields.Float(compute="_compute_grand_totals")
    hsn_code = fields.Integer(string="HSN Code",related='hsn_code_id.code')

    @api.depends('amount', 'qty','gst_breakup_cgst','gst_breakup_sgst','gst_breakup_igst')
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

    @api.depends('charge_id', 'invoice_id.gst_rate', 'invoice_id.gst_state',
                 'invoice_id.location_id', 'invoice_id.is_gst_applicable')
    def _compute_gst_amounts(self):
        for record in self:
            cgst = sgst = igst = 0.0

            # Iterate over all GST rates
            gst_rates = record.invoice_id.gst_rate
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
                    if record.invoice_id.gst_state == record.invoice_id.location_id.state_id.name:
                        cgst += (cgst_bifurcation / 100) * record.amount
                        sgst += (sgst_bifurcation / 100) * record.amount

                    # Calculate IGST if the supply is outside the state or GST is applicable
                    elif record.invoice_id.gst_state != record.invoice_id.location_id.state_id.name or record.invoice_id.is_gst_applicable == 'yes':
                        igst += (total_gst_rate / 100) * record.amount

            # Update the computed values
            record.gst_breakup_cgst = cgst
            record.gst_breakup_sgst = sgst
            record.gst_breakup_igst = igst
