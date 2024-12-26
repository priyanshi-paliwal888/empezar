# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ContainerDetails(models.Model):
    _inherit = "container.details"

    # balance = fields.Integer(string="Balance", compute="_compute_balance")
    #
    # @api.depends('container_qty')
    # def _compute_balance(self):
    #     """
    #         Compute the balance for the container_size_type
    #     """
    #     move_in = self.env['move.in'].search([]).mapped('container')
    #     move_out = self.env['move.out'].search([]).mapped('container_id').mapped('name')
    #
    #     self.balance = 0
    #
    #     for container in self.booking_id.container_numbers:
    #         container_name = str(container.name).split(' ')[0]
    #         container_master = self.env['container.master'].search([
    #             ('name', '=', container_name)
    #         ])
    #         for record in self:
    #             if (container_master.type_size.name == record.container_size_type.name and
    #                     container_name not in move_in and
    #                     container_name not in move_out):
    #                 record.balance += 1

    @api.constrains('container_qty')
    def _check_container_qty(self):
        """
            check container_qty is valid or not
        """
        for rec in self:
            if not (1 <= rec.container_qty <= 999):
                raise ValidationError('Container Quantity must be between 1 and 999.')

            move_in = self.env['move.in'].search([]).mapped('container')
            move_out = self.env['move.out'].search([]).mapped('container_id').mapped('name')

            container_list = []
            for container in rec.booking_id.container_numbers:
                container_name = str(container.name).split(' ')[0]
                if (container_name in move_in and
                        container_name in move_out):
                    container_list.append(container_name)
            container_master = self.env['container.master'].search([
                ('type_size.name', '=', rec.container_size_type.name)
            ])
            qty = 0
            for container in container_master:
                if container.name in container_list:
                    qty += 1
            if qty > rec.container_qty:
                raise ValidationError(
                    f'Container Quantity must be greater or equal to {qty} because Container Type/Size used in Move In or Move Out.')

    @api.model
    def unlink(self):
        move_in_model = self.env['move.in']
        move_out_model=self.env['move.out']
        for record in self:
            move_in_records = move_in_model.search(
                [('movement_type', '=', 'repo'), ('type_size_id', '=', record.container_size_type.id),('booking_no_id','=', record.booking_id.booking_no)])
            if move_in_records:
                raise ValidationError(
                    _("You cannot delete this record because this matching type size is used in MOVE IN."))
            move_out_records = move_out_model.search(
                [('movement_type', '=', 'repo'), ('type_size_id', '=', record.container_size_type.id),('booking_no_id','=', record.booking_id.booking_no)]
            )
            if move_out_records:
                raise ValidationError(
                    _("You cannot delete this record because this matching type size is used in MOVE OUT.")
                )
            return super(ContainerDetails, self).unlink()