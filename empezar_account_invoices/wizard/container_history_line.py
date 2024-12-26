from odoo import fields, models, api, _
from lxml import etree

class MoveInHistoryLineWizard(models.TransientModel):
    _name = 'move.in.history.line.wizard'
    # _description = 'Move In/Out History Line'

    wizard_id = fields.Many2one('container.history.wizard', string="Wizard", readonly="1" )
    location_id = fields.Char(string="Location", readonly="1")
    move_in_date_time = fields.Datetime(string="Move In Date",readonly="1")
    move_out_date_time = fields.Datetime(string="Move Out Date",readonly="1")
    move_in_url = fields.Html( string='Move IN URL', store=False)
    move_out_url = fields.Html(string='Move OUT URL', store=False)



