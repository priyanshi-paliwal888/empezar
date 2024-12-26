from odoo import fields, models, api


class HoldReleaseContainers(models.Model):
    _name = "hold.release.containers"
    _description = "Hold Release Containers"
    _rec_name = "inventory_id"

    container_id = fields.Many2one('container.master', string="Container No.",related='inventory_id.container_master_id', ondelete='cascade')
    inventory_id = fields.Many2one('container.inventory', string="Inventory No.", ondelete='cascade')
    location_id = fields.Many2one('res.company', string="Location", domain="[('parent_id','!=',False)]", required=True)
    type_size = fields.Many2one(related='container_id.type_size', string="Type/Size")
    hold_date = fields.Datetime(string="Hold Date Range", required=True)
    hold_reason_id = fields.Many2one('hold.reason', string="Hold Reason", required=True)
    remarks = fields.Text(string="Remark")


    def action_container_release(self):
        """ Open a wizard form to release the container.
            Returns:
                dict: Action dictionary for opening a new form view.
        """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Release Container',
            'res_model': 'release.container.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {
                'default_display_name': self.inventory_id.name,
                'default_release_container_id': self.id,
            }
        }

    @api.model
    def download_xlsx_file(self):
        """ Action to download a sample Excel file for holding containers.
            Returns:
                dict: Action dictionary for opening a URL in a new window.
        """
        return {
            'type': 'ir.actions.act_url',
            'url': '/empezar_inventory/static/src/document/hold_containers_sample.xlsx',
            'target': 'new',
        }