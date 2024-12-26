from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class CreditNoteInvoiceCharge(models.Model):
    _name = "credit.note.invoice.charge"
    _description = "Credit Note Invoice Charge"
    _order = "create_date desc"

    credit_note_invoice_id = fields.Many2one('credit.note.invoice', string="Invoice")
    charge_id = fields.Many2one('product.template', string="Charge")
    charge_name = fields.Char("Charge Name",related='charge_id.name')
    hsn_code_id = fields.Many2one("master.hsn.code", string="HSN Code" ,related='charge_id.hsn_code')
    amount = fields.Integer(string="Amount", required=True)
    qty = fields.Integer(string="Qty")
    total_amount = fields.Float("Total Amount", compute="_compute_totals", store=True)
    gst_breakup_cgst = fields.Float("GST Breakup (CGST)", default=0, compute='_compute_gst_amounts', store=True)
    gst_breakup_sgst = fields.Float("GST Breakup (SGST)", default=0, compute='_compute_gst_amounts', store=True)
    gst_breakup_igst = fields.Float("GST Breakup (IGST)", default=0, compute='_compute_gst_amounts', store=True)
    grand_total = fields.Float(compute="_compute_grand_totals", store=True)
    size = fields.Char(string="Size")
    hsn_code = fields.Integer(string="HSN Code", related='hsn_code_id.code')

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

    @api.depends('charge_id', 'credit_note_invoice_id.gst_rate',
                 'credit_note_invoice_id.location_id')
    def _compute_gst_amounts(self):
        for record in self:
            cgst = sgst = igst = 0.0

            # Iterate over all GST rates
            gst_rates = record.credit_note_invoice_id.gst_rate
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
                    if record.credit_note_invoice_id.supply_to_state == record.credit_note_invoice_id.location_id.state_id.name:
                        cgst += (cgst_bifurcation / 100) * record.amount
                        sgst += (sgst_bifurcation / 100) * record.amount

                    # Calculate IGST if the supply is outside the state or GST is applicable
                    elif record.credit_note_invoice_id.supply_to_state != record.credit_note_invoice_id.location_id.state_id.name:
                        igst += (total_gst_rate / 100) * record.amount

            # Update the computed values
            record.gst_breakup_cgst = cgst
            record.gst_breakup_sgst = sgst
            record.gst_breakup_igst = igst

    @api.onchange('amount')
    @api.constrains('amount')
    def check_amount_validation(self):
        for rec in self:
            if rec.amount < 0:
                raise ValidationError(_("Amount cannot be a negative value"))
            credit_note_invoice = self.env['move.in.out.invoice'].search(
                [('invoice_number', '=', rec.credit_note_invoice_id.invoice_reference_no)], limit=1).mapped('charge_ids')
            total_amount = sum(charge.amount for charge in credit_note_invoice)

            credit_note_invoice_amount =  self.env['credit.note.invoice'].search([('invoice_reference_no','=', self.credit_note_invoice_id.invoice_reference_no),('credit_note_status','=','active')]).mapped('total_charge_amount')
            credit_note_amount = sum(credit_note_invoice_amount)

            if credit_note_amount > total_amount:
                raise ValidationError(_("Cannot create credit note. The amount will exceed the available balance for the invoice."))