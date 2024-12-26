from odoo import fields, models

class MasterComponent(models.Model):
    _name = "key.value"
    _description = "Key Value"
    _rec_name = "name"
    """Model to store the key value."""

    name = fields.Char("Key Value")
