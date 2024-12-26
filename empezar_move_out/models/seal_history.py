from odoo import models, fields

class SealHistory(models.Model):
    _name = 'seal.history'
    _description = 'Seal Status History'
    
    seal_id = fields.Many2one('seal.management', string='Seal', ondelete='cascade')
    rec_status = fields.Selection(
        [
            ("available", "Available"),
            ("used", "Used"),
            ("damaged", "Damaged"),
        ],
        string="STATUS",
    )
    activity = fields.Char(string="ACTIVITY")
    container_number = fields.Char(string="CONTAINER No.")
    user_name = fields.Char(string="USER NAME")
    date_changed = fields.Datetime(string='DATE/TIME', default=fields.Datetime.now)