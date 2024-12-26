# -*- coding: utf-8 -*-
from odoo import models, fields, api,_


class UnlinkContainerWizard(models.TransientModel):
    _name = 'unlink.container.wizard'
    _description = 'Unlink Container Wizard'

    container_ids = fields.Many2many('container.number',string='Container')
    unlink_reason = fields.Many2one('unlink.reason',string="Unlink Reason")

    @api.model
    def default_get(self, fields):
        """
        Override of default_get method to include additional default values based on context.

        :param fields: List of fields for which default values are requested.
        :return: Dictionary of default values for the requested fields, including 'container_ids'
                 if provided in the context.
        """
        res = super().default_get(fields)
        container_ids = self._context.get('container_ids')
        if container_ids:
            res['container_ids'] = container_ids
        return res

    def unlink_containers(self):
        """
            wizard action for unlink  containers
        """
        return {
            'type': 'ir.actions.act_window',
            'name': _('Confirm Unlink Containers'),
            'res_model': 'unlink.container.confirmation',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_container_ids': self.container_ids.ids,
                'default_unlink_reason': self.unlink_reason.id
            },
        }
