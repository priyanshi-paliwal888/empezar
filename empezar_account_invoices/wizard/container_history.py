from odoo import fields, models, api, _

class MoveInHistoryWizard(models.TransientModel):
    _name = 'container.history.wizard'
    _description = 'Container History Wizard'

    history_line_ids = fields.One2many(
        'move.in.history.line.wizard', 'wizard_id', string='')



