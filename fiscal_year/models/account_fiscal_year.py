# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.addons.empezar_base.models.contrainer_type_edi import ContainerTypeEdi
from odoo.addons.empezar_base.models.res_users import ResUsers


class AccountFiscalYear(models.Model):
    _name = 'account.fiscal.year'
    _description = 'Fiscal Year'

    name = fields.Char(string='Fiscal Year', required=True, size=128)
    date_from = fields.Date(string='Start Date', required=True,
        help='Start Date, included in the fiscal year.')
    date_to = fields.Date(string='End Date', required=True,
        help='Ending Date, included in the fiscal year.')
    company_id = fields.Many2one('res.company', string='Company', required=True,
        default=lambda self: self.env.company)
    active = fields.Boolean("Active", default=True)
    rec_status = fields.Selection([
        ('active', 'Active'),
        ('disable', 'Disable'),
    ], default="active", compute="_check_active_records", string="Status")
    display_create_info = fields.Char(compute="_get_create_record_info")
    display_modified_info = fields.Char(compute="_get_modify_record_info")

    def _get_create_record_info(self):
        """
        Assign create record log string to the appropriate field.
        :return: none
        """
        for rec in self:
            if rec.env.user.tz and rec.create_uid:
                tz_create_date = ResUsers.convert_datetime_to_user_timezone(rec.env.user, rec.create_date)
                create_uid_name = rec.create_uid.name
                if tz_create_date:
                    rec.display_create_info = ResUsers.get_user_log_data(rec, tz_create_date, create_uid_name)
            else:
                rec.display_create_info = ''

    def _get_modify_record_info(self):
        """
            Assign update record log string to the appropriate field.
            :return: none
        """
        for rec in self:
            if rec.env.user.tz and rec.write_uid:
                tz_write_date = ResUsers.convert_datetime_to_user_timezone(rec.env.user, rec.write_date)
                write_uid_name = rec.write_uid.name
                if tz_write_date:
                    rec.display_modified_info = ResUsers.get_user_log_data(rec, tz_write_date, write_uid_name)
            else:
                rec.display_modified_info = ''

    def _check_active_records(self):
        ContainerTypeEdi.check_active_records(self)

    @api.constrains('date_from', 'date_to', 'company_id')
    def _check_dates(self):
        '''
        Check interleaving between fiscal years.
        There are 3 cases to consider:

        s1   s2   e1   e2
        (    [----)----]

        s2   s1   e2   e1
        [----(----]    )

        s1   s2   e2   e1
        (    [----]    )
        '''
        for fy in self:
            # Starting date must be prior to the ending date
            date_from = fy.date_from
            date_to = fy.date_to
            if date_to < date_from:
                raise ValidationError(_('End Date should be less than Start Date.'))
            domain = [
                ('id', '!=', fy.id),
                ('company_id', '=', fy.company_id.id),
                '|', '|',
                '&', ('date_from', '<=', fy.date_from), ('date_to', '>=', fy.date_from),
                '&', ('date_from', '<=', fy.date_to), ('date_to', '>=', fy.date_to),
                '&', ('date_from', '<=', fy.date_from), ('date_to', '>=', fy.date_to),
            ]
            if self.search_count(domain) > 0:
                raise ValidationError(_('Fiscal year should not overlap. Please enter a valid Fiscal year.'))

    @api.constrains('name')
    def _check_fiscal_year(self):
        for rec in self:
            existing_fiscal_year = rec.env['account.fiscal.year'].search([
                ('id', '!=', rec.id)
            ])
            fiscal_years = existing_fiscal_year.mapped('name')
            if rec.name in fiscal_years:
                raise ValidationError(
                    _(f"{rec.name} already exists. Please enter a new fiscal year.")
                )
