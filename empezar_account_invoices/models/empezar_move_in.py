from odoo import fields, models, api,_


class MoveIn(models.Model):
    _inherit = "move.in"

    is_invoice_applicable = fields.Boolean(string="Is Invoice Applicable",
                                           compute="_compute_is_invoice_applicable",
                                           default=False)
    is_invoice_created = fields.Boolean(string="Is Invoice Created", default=False)
    invoice_ids = fields.One2many('move.in.out.invoice','move_in_id', string="Invoice Number")

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
        """ Create the move in record"""
        move_in_record = super().create(vals)
        # Create a corresponding pending invoice record
        container_details = f"{move_in_record.container} {move_in_record.type_size_id.company_size_type_code}"
        self.env['pending.invoices'].create({
            'movement_type': 'move_in',
            'move_in_id': move_in_record.id,
            'booking_no_id':move_in_record.booking_no_id.id,
            'shipping_line_id': move_in_record.shipping_line_id.id,
            'location_id': move_in_record.location_id.id,
            'billed_to_party': move_in_record.billed_to_party.id,
            'container_number': move_in_record.container,
            'container_details': container_details,
            'movement_date_time': move_in_record.move_in_date_time,
            'invoice_type': 'lift_off'
        })

        return move_in_record

    @api.model
    def write(self, vals):
        # Store the previous state to update pending invoices later
        move_in_ids = self.ids
        result = super().write(vals)

        if move_in_ids:
            pending_invoices = self.env['pending.invoices'].search([('move_in_id', 'in', move_in_ids)])
            for invoice in pending_invoices:
                # Update the corresponding fields in pending invoices
                if 'shipping_line_id' in vals:
                    invoice.shipping_line_id = vals.get('shipping_line_id')
                if 'billed_to_party' in vals:
                    invoice.billed_to_party = vals.get('billed_to_party')
                if 'move_in_date_time' in vals:
                    invoice.movement_date_time = vals.get('move_in_date_time')
        return result

    def download_help_icon(self):
        view_id = self.env.ref('empezar_account_invoices.move_in_tree_view_inherit').id
        return self.env['help.document'].download_help_doc(view_id=view_id)

    def action_view_invoices(self):
        """Define the action to open the invoices page with additional context"""

        self.ensure_one()
        action = self.env["ir.actions.actions"].with_context(is_invoice= True)._for_xml_id("empezar_account_invoices.invoices_move_action")

        if isinstance(action.get('context'), str):
            action['context'] = {}

        action['domain'] = ['|',('move_in_ids', 'in', self.ids), ('move_in_id', '=', self.id)]
        action['context'] = {
            'default_move_in_id': self.id,
        }
        return action
