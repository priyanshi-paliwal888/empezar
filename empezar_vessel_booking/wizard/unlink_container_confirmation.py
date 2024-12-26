# -*- coding: utf-8 -*-
from odoo import models,fields


class UnlinkContainerConfirmation(models.TransientModel):
    _name = 'unlink.container.confirmation'
    _description = 'Unlink Container Confirmation'

    container_ids = fields.Many2many('container.number',string='Container')
    unlink_reason = fields.Many2one('unlink.reason',string="Unlink Reason")

    def confirm_unlink(self):
        """
            wizard action for confirm the unlink container number
             :return:
        """
        if self.unlink_reason.update_quantity == True:
            qty_dict = {}
            for container in self.container_ids:
                container.unlink_reason = self.unlink_reason
                container.is_unlink = False
                container.is_unlink_non_editable = True

                main_parts = [str(container.name).split(' ')[0]]
                container_data = self.env['container.master'].search([('name', 'in', main_parts)])

                if container_data:
                    type_size_name = container_data.type_size.name
                    if type_size_name not in qty_dict:
                        qty_dict[type_size_name] = 0
                    qty_dict[type_size_name] += 1

            for type_size_name, unlink_qty in qty_dict.items():
                container_details = self.env['container.details'].search([
                    ('booking_id', '=', self.container_ids[0].vessel_booking_id.id),
                    ('container_size_type.name', '=', type_size_name)
                ])

                for container_detail in container_details:
                    new_quantity = container_detail.container_qty - unlink_qty
                    container_detail.write({'container_qty': new_quantity})
        else:
            for container in self.container_ids:
                container.unlink_reason = self.unlink_reason
                container.is_unlink = False
                container.is_unlink_non_editable = True
        return {'type': 'ir.actions.act_window_close'}
