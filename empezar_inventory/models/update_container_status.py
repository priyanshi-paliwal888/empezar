# -*- coding: utf-8 -*-

from odoo import fields, models, api
from .upload_inventory import UploadInventory


class UploadContainerStatus(models.Model):

    _name = "update.container.status"
    _description = "Update Container Status"

    name = fields.Char(string="File Name")
    upload_inventory_file = fields.Binary(string="Upload File",
                                          help="Only XLS or XLSX files with max size of 5 MB and"
                                                                        " having max 200 entries.",
                                          required=True, copy=False, exportable=False)
    upload_id = fields.Char(string="Upload ID", compute='set_upload_id')
    uploaded_by = fields.Char(string="Uploaded By")
    uploaded_on = fields.Datetime(string="Uploaded On")
    rec_status = fields.Selection([
        ('success', 'Success'),
        ('error', 'Error')
    ])

    @api.model
    def download_xlsx_file(self, **kwargs):
        return {
            'type': 'ir.actions.act_url',
            'url': '/empezar_inventory/static/src/document/update_container_status_sample.xlsx',
            'target': 'new',
        }

    def set_upload_id(self):
        """
        Set upload id values.
        :return:
        """
        UploadInventory.set_upload_id(self)
