""" -*- coding: utf-8 -*- """
from odoo import fields, models, _,api


class ContainerDetailsWizard(models.Model):
    _name = 'view.update.allocation'
    _description = 'Container Details Wizard'

    delivery_order_id = fields.Many2one('delivery.order', string='Delivery Order')
    allocation_id = fields.Many2one('update.allocation.wizard', string='Seal', ondelete='cascade')

    container_details = fields.One2many(related='delivery_order_id.container_details',
                                        readonly=False)

    container_type_size = fields.Char(string="Container Type Size", store=True)
    yard = fields.Char(string="Yard", store=True)
    count = fields.Integer(string="Count", store=True)
    is_from_location = fields.Boolean(string="Is From Location", store=True)