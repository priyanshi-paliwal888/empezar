from odoo import models, api


class ContainerFacilities(models.Model):
    _inherit = "container.facilities"

    @api.model
    def default_get(self, fields_list):
        """Set default values for fields, including 'facility_type' based on context flags.
        """
        res = super().default_get(fields_list)
        facility_type = ''
        port = False
        if self.env.context.get('is_from_move_out'):
            if self.env.context.get('is_from_cfs_icd'):
                facility_type = 'cfs'
            if self.env.context.get('is_from_terminal'):
                facility_type = 'terminal'
                port = self.env.context.get('port')
            if self.env.context.get('is_from_empty_yard'):
                facility_type = 'empty_yard'
            res.update({
                'facility_type': facility_type,
                'port': port
            })
        return res
