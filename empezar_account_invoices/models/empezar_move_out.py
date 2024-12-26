from odoo import fields, models, api,_


class MoveOut(models.Model):
    _inherit = "move.out"

    is_invoice_applicable = fields.Boolean(string="Is Invoice Applicable",
                                           compute="_compute_is_invoice_applicable",
                                           default=False)
    is_invoice_created = fields.Boolean(string="Is Invoice Created", default=False)
    invoice_ids = fields.One2many('move.in.out.invoice', 'move_out_id', string="Invoice Number")

    @api.depends('location_id', 'shipping_line_id')
    def _compute_is_invoice_applicable(self):
        """
        Compute the invoice applicable or not for move in records
        based on location.
        """
        for record in self:
            record.is_invoice_applicable = False
            if record.location_id and record.shipping_line_id:
                mapped_lines = record.location_id.invoice_setting_ids.filtered(
                    lambda line: line.inv_shipping_line_id == record.shipping_line_id
                )
                if mapped_lines:
                    record.is_invoice_applicable = True

    @api.model
    def create(self, vals):
        """ Create the move out record """
        move_out_record = super().create(vals)

        # Create a corresponding pending invoice record
        container_details = f"{move_out_record.container_id.name} {move_out_record.company_size_type}"
        self.env['pending.invoices'].create({
            'movement_type': 'move_out',
            'booking_no_id': move_out_record.booking_no_id.id,
            'move_out_id': move_out_record.id,
            'shipping_line_id': move_out_record.shipping_line_id.id,
            'location_id': move_out_record.location_id.id,
            'billed_to_party': move_out_record.billed_to_party.id,
            'container_number': move_out_record.container_id.name,
            'container_details': container_details,
            'movement_date_time': move_out_record.move_out_date_time,
            'invoice_type': 'lift_on'
        })

        return move_out_record

    @api.model
    def write(self, vals):
        # Store the previous state to update pending invoices later
        move_out_ids = self.ids
        result = super().write(vals)

        if move_out_ids:
            pending_invoices = self.env['pending.invoices'].search([('move_out_id', 'in', move_out_ids)])
            for invoice in pending_invoices:
                # Update the corresponding fields in pending invoices
                if 'shipping_line_id' in vals:
                    invoice.shipping_line_id = vals.get('shipping_line_id')
                if 'billed_to_party' in vals:
                    invoice.billed_to_party = vals.get('billed_to_party')
                if 'move_out_date_time' in vals:
                    invoice.movement_date_time = vals.get('move_out_date_time')
        return result

    def download_help_icon(self):
        view_id = self.env.ref('empezar_account_invoices.move_in_tree_view_inherit').id
        return self.env['help.document'].download_help_doc(view_id=view_id)

    def action_view_invoices(self):
        """Define the action to open the invoices page with additional context"""

        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("empezar_account_invoices.invoices_move_action")

        if isinstance(action.get('context'), str):
            action['context'] = {}

        action['domain'] = ['|',('move_out_ids', 'in', self.ids), ('move_out_id', '=', self.id)]
        action['context'] = {
            'default_move_out_id': self.id,
        }
        return action
