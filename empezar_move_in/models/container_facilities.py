# -*- coding: utf-8 -*-
from odoo import models, api


class ContainerFacilities(models.Model):

    _inherit = "container.facilities"

    @api.model
    def default_get(self, fields_list):
        """
        Set default facility type cfs when record create from cfs.
        """
        res = super().default_get(fields_list)
        if self._context.get("is_from_move_in"):
            if self._context.get("cfs_move_in"):
                res['facility_type'] = 'cfs'
            if self._context.get("terminal_move_in"):
                res['facility_type'] = 'terminal'
            if self._context.get("empty_yard_move_in"):
                res['facility_type'] = 'empty_yard'
        return res
