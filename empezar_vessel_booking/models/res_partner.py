# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class ResPartner(models.Model):

    _inherit = "res.partner"

    @api.model
    def default_get(self, fields_list):
        """
            Set parties from main company
            :param fields_list
            :return:
        """
        res = super().default_get(fields_list)
        if self.env.context.get('is_from_booking'):
            # Set default values for party_type_ids
            parties_type_transporter = self.env.ref('empezar_base.cms_parties_type_5').id
            res.update({
                'parties_type_ids': [(6, 0, [parties_type_transporter])],
            })
        return res

    @api.model_create_multi
    def create(self, vals_list):
        """
        Assign mandatory field values while create a record from vessel booking.
        :param vals_list:
        :return:
        """
        if self._context.get('is_from_booking'):
            transporter_type = self.env.ref('empezar_base.cms_parties_type_5').id
            cms_parties_tag_id = self.env.ref(
                "empezar_base.res_partner_cms_parties_tag_1"
            ).id
            for vals in vals_list:
                vals.update({
                    "is_cms_parties": True,
                    "name": vals.get("name"),
                    "party_name": vals.get("name"),
                    "category_id": [cms_parties_tag_id],
                    'parties_type_ids': [(6, 0, [transporter_type])],
                })
        res = super().create(vals_list)
        return res

    def write(self, vals):
        """
        update the name fields while update the shipping line name from shipping line view.
        :param vals:
        :return:
        """
        if self._context.get("is_from_booking") and vals.get("party_name"):
            vals.update({"name": vals["party_name"]})
        res = super().write(vals)
        return res
