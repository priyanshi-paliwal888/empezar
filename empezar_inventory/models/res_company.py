from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    @api.constrains('active', 'name')
    def _check_location_name(self):
        for record in self:
            if not record.active:
                if record.name:
                    company = self.env['container.inventory'].search([('location_id.name', '=', record.name)], limit=1)
                    if company:
                        raise ValidationError(
                    _('Location "%s"  cannot be disabled as containers for this location are present in the inventory.') % record.name)
