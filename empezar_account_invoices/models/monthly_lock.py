# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from lxml import etree
from odoo.addons.empezar_base.models.res_users import ResUsers


class MonthlyLock(models.Model):

    _name = "monthly.lock"
    _description = "Monthly Lock"
    _rec_name="invoice_type"
    _order = "create_date desc"

    def _default_previous_month(self):
        # Get the current date
        today = datetime.today()
        # Calculate the first day of the current month
        first_day_of_this_month = today.replace(day=1)
        # Subtract one day to get the last day of the previous month
        last_day_of_previous_month = first_day_of_this_month - timedelta(days=1)
        # Return the month in "MM" format
        return last_day_of_previous_month.strftime("%m")

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
        ],
        string="Month",
        default=_default_previous_month,
    )

    location_id = fields.Many2one('res.company', string="Location", domain="[('parent_id', '!=', False)]")
    fiscal_year = fields.Many2one('account.fiscal.year', string="Fiscal Year")
    history = fields.Selection(
        [
            ("hide", "Hide"),
            ("show", "Show"),
        ], string="History", default="hide", required=True)
    is_locked = fields.Boolean("Is Locked")
    history_line_ids = fields.One2many('monthly.lock.history', 'monthly_lock_id',
                                       string="History Lines")
    invoice_type = fields.Selection(
        [
            ("invoice", "Invoices"),
            ("credit", "Credit Notes"),
        ], string="Type")
    display_create_info = fields.Char(compute="_get_create_record_info")
    display_modified_info = fields.Char(compute="_get_modify_record_info")
    display_sources = fields.Char(string="Source", readonly=True, default="Web")
    active = fields.Boolean(string="Active", default=True)

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

    def action_lock_invoice(self):
        """Open wizard to lock the invoices for multiple records."""
        location_name = self.location_id.name if self.location_id else _("")
        invoice_type = self.invoice_type
        if not location_name and not invoice_type:
            name = _("Lock Invoices/Credit Notes")
        else:
            invoice_type_dict = dict(self._fields['invoice_type'].selection)
            invoice_type_value = invoice_type_dict.get(self.invoice_type, "")
            name = _(
                f"Lock {location_name or ''}'s {invoice_type_value or ''} ") if location_name and invoice_type else _(
                f"Lock {location_name or ''} {invoice_type_value or ''} ")

        # Handle both active_id and active_ids
        active_ids = self._context.get('active_ids', [])
        active_id = self._context.get('active_id')
        if active_id and active_id not in active_ids:
            active_ids.append(active_id)

        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('empezar_account_invoices.view_monthly_lock_wizard_form').id,
            'res_model': 'monthly.lock.wizard',
            'target': 'new',
            'context': {
                'default_action': 'lock',
                'active_ids': active_ids,
                'default_invoice_type': self.invoice_type,
            },
        }

    def action_unlock_invoice(self):
        """Open wizard to unlock the invoices."""
        location_name = self.location_id.name if self.location_id else _("")
        invoice_type = self.invoice_type
        if not location_name and not invoice_type:
            name = _("Unlock Invoices/Credit Notes")
        else:
            invoice_type_dict = dict(self._fields['invoice_type'].selection)
            invoice_type_value = invoice_type_dict.get(self.invoice_type, "")
            name = _(
                f"Unlock {location_name}'s {invoice_type_value} ") if location_name and invoice_type else _(
                f"Unlock {location_name or ''} {invoice_type_value or ''}")

        # Handle both active_id and active_ids
        active_ids = self._context.get('active_ids', [])
        active_id = self._context.get('active_id')
        if active_id and active_id not in active_ids:
            active_ids.append(active_id)

        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('empezar_account_invoices.view_monthly_unlock_wizard_form').id,
            'res_model': 'monthly.lock.wizard',
            'target': 'new',
            'context': {
                'default_action': 'unlock',
                'active_ids': active_ids,
                'default_invoice_type': self.invoice_type,
            },
        }

    def action_view_monthly_lock_history(self):
        """Open a wizard or a modal to show lock/unlock history."""
        self.ensure_one()
        location_name = self.location_id.name if self.location_id else _("")
        # invoice_type = self.invoice_type
        invoice_type_dict = dict(self._fields['invoice_type'].selection)
        invoice_type_value = invoice_type_dict.get(self.invoice_type, "")
        
        return {
            'name': _(f"{location_name}'s {invoice_type_value} History"),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'res_model': 'monthly.lock.history',
            'domain': [('monthly_lock_id', '=', self.id)],
            'context': {'default_monthly_lock_id': self.id},
            'target': 'new',
        }

    @api.model
    def create(self, vals):
        # Check if a record with the same location and invoice_type already exists
        if vals.get('location_id') and vals.get('invoice_type'):
            existing_record = self.search([('location_id', '=', vals['location_id']),
                                           ('month', '=', vals['month']),
                                           ('invoice_type', '=', vals['invoice_type']),
                                           ('fiscal_year', '=', vals['fiscal_year']),
                                           ('id', '!=', self.id)], limit=1)
            if existing_record:
                raise ValidationError(
                    _("An invoice of type '%s' for this location already exists in month '%s'.") % (
                        vals['invoice_type'], vals['month']))
        return super().create(vals)

    def write(self, vals):
        # Check if a record with the same location and invoice_type already exists when updating
        if vals.get('location_id') and vals.get('invoice_type'):
            existing_record = self.search([('location_id', '=', vals['location_id']),
                                           ('invoice_type', '=', vals['invoice_type']),
                                           ('month', '=', vals['month']),
                                           ('fiscal_year', '=', vals['fiscal_year']),
                                           ('id', '!=', self.id)], limit=1)
            if existing_record:
                raise ValidationError(
                    _("An invoice of type '%s' for this location already exists in month '%s'.") % (
                        vals['invoice_type'], vals['month']))
        return super().write(vals)


class MonthlyLockHistory(models.Model):
    _name = "monthly.lock.history"
    _description = "Monthly Lock History"

    monthly_lock_id = fields.Many2one('monthly.lock', string="Monthly Lock", required=True, ondelete='cascade')
    username = fields.Char(string="Username", required=True)
    date_time = fields.Datetime(string="Date/Time", required=True, default=fields.Datetime.now)
    action = fields.Selection([('lock', 'Locked'), ('unlock', 'Unlocked')], string="Action", required=True)
    remarks = fields.Char(string="Remarks", size=64)
    invoice_type = fields.Selection(
        [
            ("invoice", "Invoice"),
            ("credit", "Credit"),
        ], string="Type")
    display_remarks = fields.Char(
        string="Remarks",
        compute="_compute_display_remarks",
        store=False,
    )

    @api.depends('remarks')
    def _compute_display_remarks(self):
        for record in self:
            record.display_remarks = record.remarks if record.remarks else "-"
