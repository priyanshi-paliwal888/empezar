# -*- coding: utf-8 -*-
from odoo import models, api


class ResPartner(models.Model):

    _inherit = "res.partner"

    @api.model
    def default_get(self, fields_list):
        """
        Set default facility type cfs when record create from cfs.
        """
        res = super().default_get(fields_list)
        if self._context.get("is_from_billed_to_party"):
            res['is_this_billed_to_party'] = "yes"
        return res

    @api.model_create_multi
    def create(self, vals_list):
        """
        Assign mandatory field values while create a record from Delivery Order
        :param vals_list:
        :return:
        """

        if self._context.get('is_from_billed_to_party'):
            for vals in vals_list:
                vals.update({
                    "is_cms_parties": True,
                    "name": vals.get("name"),
                    "party_name": vals.get("name"),
                })

        res = super().create(vals_list)
        return res
