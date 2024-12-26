# -*- coding: utf-8 -*-

from odoo import fields, models


class ModeOptions(models.Model):

    _name = "mode.options"
    _description = "Mode Options"

    name = fields.Char(string="Name")


class LadenStatusOptions(models.Model):

    _name = "laden.status.options"
    _description = "Laden Status Options"

    name = fields.Char(string="Name")


class OperationsOptions(models.Model):

    _name = "operations.options"
    _description = "Operations Options"

    name = fields.Char(string="Name")


class GatePassOptions(models.Model):

    _name = "gate.pass.options"
    _description = "GatePass Options"

    name = fields.Char(string="Name")


class InvoiceApplicableOptions(models.Model):

    _name = "invoice.applicable.options"
    _description = "Invoice Applicable Options"

    name = fields.Char(string="Name")


class PaymentModeOptions(models.Model):

    _name = "payment.mode.options"
    _description = "Payment Mode Options"

    name = fields.Char(string="Name")
