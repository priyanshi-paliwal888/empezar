# -*- coding: utf-8 -*-
from odoo import fields, models, api


class ContainerNumber(models.Model):
    _inherit = "container.number"

    # move_in_datetime = fields.Datetime(string="Move In Date/Time",
    #                                    compute="compute_update_container_dates")
    move_out_datetime = fields.Datetime(string="Move Out Date/Time", compute="compute_update_container_dates")

    def compute_update_container_dates(self):
        """
           update the Date Time Depends on move In/ move Out container numbers
        """
        for record in self:
            # record.move_in_datetime = False
            record.move_out_datetime = False
            container_number = record.mapped('name')

            number = container_number[0].split()[0]
            # move_in_records = self.env['move.in'].search([('container', '=', number)],order='id desc',limit=1)
            move_out_records = self.env['move.out'].search([('container_id', '=', number)], order='id desc',limit=1)

            # if move_in_records:
            #     record.move_in_datetime = move_in_records.move_in_date_time
            if move_out_records:
                record.move_out_datetime = move_out_records.move_out_date_time
