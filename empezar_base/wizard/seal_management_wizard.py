# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import psycopg2, logging

_logger = logging.getLogger(__name__)


class SealManagementWizard(models.TransientModel):
    _name = 'seal.management.wizard'
    _description = "Seal"

    location = fields.Many2one('res.company', string="Location", domain="[('parent_id','!=', False)]")
    shipping_line_id = fields.Many2one('res.partner', domain="[('is_shipping_line', '=', True)]",
                                       string="Shipping Line")
    prefix = fields.Char(string="Prefix", size=8)
    start_range = fields.Char(string="Start Range", size=16, required=True)
    end_range = fields.Char(string="End Range", size=16, required=True)

    def action_create(self):
        try:
            vals = []
            seal_number_list = []

            # Prepare values for seal numbers
            for rec in range(int(self.start_range), int(self.end_range)+1):
                seal_number = str(rec)
                if self.prefix:
                    seal_number = self.prefix + str(rec)
                seal_number_vals = {
                    'shipping_line_id': self.shipping_line_id.id,
                    'location': self.location.id,
                    'seal_number': seal_number,
                    'rec_status': 'available',
                }
                vals.append(seal_number_vals)
                seal_number_list.append(seal_number)

            # Create seal records
            self.create_seal_records(vals)

            # Return reload action
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }

        except psycopg2.IntegrityError as e:
            self.env.cr.rollback()
            if 'unique constraint' in str(e):
                # Handle duplicate seal numbers
                self.handle_duplicate_seal_numbers(seal_number_list)
                _logger.warning("There is some issue while generating seal number %s.", e)
            _logger.warning("There is some issue while generating seal number %s.", e)
        except Exception as e:
            self.handle_duplicate_seal_numbers(seal_number_list)
            _logger.warning("There is some issue while generating seal number %s.", e)

    def handle_duplicate_seal_numbers(self, seal_number_list):
        # Check each duplicate seal number with shipping Line, location and send email if needed
        for seal_number in seal_number_list:
            existing = self.env['seal.management'].search([
                ('seal_number', '=', seal_number),
                ('location','=', self.location.id),
                ('shipping_line_id','=', self.shipping_line_id.id)], limit=1)
            if existing:
                context = {'failure_reason': 'The data added for Seal Numbers is duplicate.'}
                ctx = dict(self.env.context)
                ctx.update(context)
                self.send_seal_failure_email(ctx)
                break  # Only send email once for the first duplicate found

        # Raise validation error indicating duplicate seal number found
        raise ValidationError(
            'Seal Number already present.')

    def create_seal_records(self, vals):
        self.env['seal.management'].create(vals)

    @api.constrains('start_range', 'end_range')
    def _check_ranges(self):
        for record in self:
            if not record.start_range.isdigit() or not record.end_range.isdigit():
                raise ValidationError(
                    _("Please add any positive numbers in range.")
                )
            if int(record.end_range) < int(record.start_range):
                raise ValidationError("End Range value cannot be less than the Start Range value.")
            if (int(record.end_range) - int(record.start_range)) > 1000:
                raise ValidationError("The number of seal records to be created should not be more than 1000.")

    @api.constrains('prefix')
    def check_prefix_validation(self):
        if self.prefix and not self.prefix.isalnum():
            raise ValidationError(
                _("Please Enter Alphanumeric Value in Prefix.")
            )

    def send_seal_failure_email(self, ctx):
        account_created_template = self.env.ref('empezar_base.email_template_seal_management')
        account_created_template.with_context(ctx).send_mail(
            self.id, force_send=True,
            raise_exception=True)
