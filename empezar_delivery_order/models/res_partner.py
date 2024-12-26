# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        parties_type = []
        if self.env.context.get('is_from_delivery'):
            if self.env.context.get('is_from_importer'):
                parties_type = self.env.ref('empezar_base.cms_parties_type_2').id
            if self.env.context.get('is_from_forwarder'):
                parties_type = self.env.ref('empezar_base.cms_parties_type_4').id
            if self.env.context.get('is_from_booking_party'):
                parties_type = self.env.ref('empezar_base.cms_parties_type_12').id
            elif self.env.context.get('is_from_exporter'):
                parties_type = self.env.ref('empezar_base.cms_parties_type_1').id

            res.update({
                 'parties_type_ids': [(6, 0, [parties_type])],
            })
        return res

    @api.model_create_multi
    def create(self, vals_list):
        """
        Assign mandatory field values while create a record from Delivery Order
        :param vals_list:
        :return:
        """

        if self._context.get('is_from_delivery'):
            parties_type = []
            if self.env.context.get('is_from_importer'):
                parties_type = self.env.ref('empezar_base.cms_parties_type_2').id
            elif self.env.context.get('is_from_forwarder'):
                parties_type = self.env.ref('empezar_base.cms_parties_type_4').id
            elif self.env.context.get('is_from_booking_party'):
                parties_type = self.env.ref('empezar_base.cms_parties_type_12').id
            elif self.env.context.get('is_from_exporter'):
                parties_type = self.env.ref('empezar_base.cms_parties_type_1').id
            cms_parties_tag_id = self.env.ref(
                "empezar_base.res_partner_cms_parties_tag_1"
            ).id

            for vals in vals_list:
                vals.update({
                    "is_cms_parties": True,
                    "name": vals.get("name"),
                    "party_name": vals.get("name"),
                    "category_id": [cms_parties_tag_id],
                    'parties_type_ids': [(6, 0, [parties_type])]
                })

        res = super().create(vals_list)
        return res
