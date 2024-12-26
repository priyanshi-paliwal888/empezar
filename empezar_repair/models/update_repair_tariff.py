from odoo import fields, models

class UpdateRepairTariff(models.Model):

    _name = "update.repair.tariff"
    _description = "Update Repair Tariff"

    damage_location = fields.Char(string="Damage Location", required=True)
    component = fields.Char(string="Component")
    damage_type = fields.Char(string="Damage Type", required=True)
    repair_type = fields.Char(string="Repair Type", required=True)
    measurement = fields.Char(string="Measurement")
    size_type = fields.Char(string="Size/Type", required=True)
    material_cost = fields.Float(string="Material Cost")
    labour_hour = fields.Float(string="Labour Hour")
    key_value = fields.Char(string="Key Value")
    limit= fields.Char(string="Limit")
    repair_code = fields.Char(string="Repair Code")

    def _compute_display_name(self):
        """Dynamic record name based on the context."""
        result = []
        for record in self:
            # Determine context for which field is being displayed
            context = self.env.context
            if context.get('show_limit'):
                record.display_name = record.limit or record.damage_type
            elif context.get('show_location'):
                record.display_name = record.damage_location or record.damage_type
            else:
                record.display_name = record.repair_code or record.damage_type
        return result