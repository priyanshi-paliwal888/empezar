# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class HelpDocument(models.Model):
    _name = 'help.document'
    _rec_name = 'master_menu'
    _description = 'Help Document'

    master_menu = fields.Selection([('shipping_lines', 'Shipping Lines'),
                                    ('container_facilities', 'Container Facilities'),
                                    ('parties', 'Parties'), ('containers', 'Containers'),
                                    ('fiscal_years', 'Fiscal Years'), ('charges', 'Charges'),
                                    ('locations', 'Locations'), ('lolo_charge', 'LOLO Charges'), ('seal', 'Seal'),('edi_settings','EDI Settings'),
                                    ('locations', 'Locations'), ('lolo_charge', 'LOLO Charges'),
                                    ('seal', 'Seal'), ('user', 'User'), ('roles', 'Roles'),
                                    ('company', 'Company'), ('upload_inventory', 'Upload Inventory'),('update_container_status','Update Container Status'),('hold_release_containers','Hold Release Containers'),
                                    ('vessel booking', 'Vessel Booking'), ('delivery_order', 'Delivery Order'), ('move_out', 'Move Out'),('monthly_lock', 'Monthly Lock'),('invoice', 'Invoice'),
                                    ('pending_invoice', 'Pending Invoice'),('repair_pending','Repair Pending'),('update_tariff','Update Tariff'),('move_in', 'Move In'),('move_in_out_invoice', 'Move In/Out Invoice'),
                                    ('credit_note','Credit Note')], string="Empezar Menu")

    file = fields.Binary('File')
    file_namex = fields.Char('Binary Name')
    company_id = fields.Many2one('res.company')

    @api.onchange('file')
    def _check_file_type(self):
        for record in self:
            if record.file:
                file_name = record.file_namex
                if not file_name.lower().endswith('.pdf'):
                    raise ValidationError("Only Pdf files are allowed.")

    @api.constrains('master_menu')
    def _existing_name(self):
        existing_names = self.env['help.document'].search([('id', '!=', self.id)])
        menus = existing_names.mapped('master_menu')
        if self.master_menu in menus:
            raise ValidationError(
                _(f"Help document records have already been created for {self.master_menu}.")
            )

    @api.model
    def download_help_doc(self, **kwargs):
        help_document_id = False
        view_id = kwargs.get('view_id')
        if view_id == self.env.ref('empezar_base.shipping_lines_tree_view').id:
            help_document_id = self.env['help.document'].sudo().search([('master_menu', '=', 'shipping_lines')],
                                                                   order='id DESC', limit=1)
        elif view_id == self.env.ref('empezar_base.container_facilities_tree_view').id:
            help_document_id = self.env['help.document'].sudo().search([('master_menu', '=', 'container_facilities')],
                                                                   order='id DESC', limit=1)
        elif view_id == self.env.ref('empezar_base.res_partner_parties_tree_view').id:
            help_document_id = self.env['help.document'].sudo().search([('master_menu', '=', 'parties')],
                                                                   order='id DESC', limit=1)
        elif view_id == self.env.ref('empezar_base.container_master_tree_view').id:
            help_document_id = self.env['help.document'].sudo().search([('master_menu', '=', 'containers')],
                                                                   order='id DESC', limit=1)
        elif view_id == self.env.ref('fiscal_year.view_account_fiscal_year_tree').id:
            help_document_id = self.env['help.document'].sudo().search([('master_menu', '=', 'fiscal_years')],
                                                                   order='id DESC', limit=1)
        elif view_id == self.env.ref('empezar_base.product_charge_template_tree_view').id:
            help_document_id = self.env['help.document'].sudo().search([('master_menu', '=', 'charges')],
                                                                   order='id DESC', limit=1)
        elif view_id == self.env.ref('empezar_base.res_company_location_tree_view').id:
            help_document_id = self.env['help.document'].sudo().search([('master_menu', '=', 'locations')],
                                                                   order='id DESC', limit=1)
        elif view_id == self.env.ref('empezar_base.lolo_charge_tree_view').id:
            help_document_id = self.env['help.document'].sudo().search([('master_menu', '=', 'lolo_charge')],
                                                                   order='id DESC', limit=1)
        elif view_id == self.env.ref('empezar_base.seal_management_tree_view').id:
            help_document_id = self.env['help.document'].sudo().search([('master_menu', '=', 'seal')],
                                                                   order='id DESC', limit=1)
        elif view_id == self.env.ref('empezar_edi.edi_settings_list_view').id:
            help_document_id = self.env['help.document'].sudo().search([('master_menu', '=', 'edi_settings')],order='id DESC', limit=1)
        elif view_id == self.env.ref('base.view_users_tree').id:
            help_document_id = self.env['help.document'].sudo().search([('master_menu', '=', 'user')],
                                                                   order='id DESC', limit=1)
        elif view_id == self.env.ref('empezar_base.inherit_res_groups_tree_view').id:
            help_document_id = self.env['help.document'].sudo().search([('master_menu', '=', 'roles')],
                                                                   order='id DESC', limit=1)
        elif view_id == self.env.ref('base.view_company_tree').id:
            help_document_id = self.env['help.document'].sudo().search([('master_menu', '=', 'company')],
                                                                   order='id DESC', limit=1)
        elif view_id == self.env.ref('empezar_inventory.upload_inventory_tree_view').id:
            help_document_id = self.env['help.document'].sudo().search([('master_menu', '=', 'upload_inventory')],
                                                                   order='id DESC', limit=1)
        elif view_id == self.env.ref('empezar_inventory.upload_container_status_tree_view').id:
            help_document_id = self.env['help.document'].sudo().search([('master_menu', '=', 'update_container_status')],
                                                                   order='id DESC', limit=1)
        elif view_id == self.env.ref('empezar_inventory.hold_release_containers_tree_view').id:
            help_document_id = self.env['help.document'].sudo().search([('master_menu', '=', 'hold_release_containers')],
                                                                   order='id DESC', limit=1)
        elif view_id == self.env.ref('empezar_vessel_booking.view_vessel_booking_tree').id:
            help_document_id = self.env['help.document'].sudo().search([('master_menu', '=', 'vessel booking')],
                                                                    order='id DESC', limit=1)
        elif view_id == self.env.ref('empezar_delivery_order.view_delivery_order_tree').id:
            help_document_id = self.env['help.document'].sudo().search([('master_menu', '=', 'delivery_order')],
                                                                    order='id DESC', limit=1)
        elif view_id == self.env.ref('empezar_move_out.view_move_out_tree').id:
            help_document_id = self.env['help.document'].sudo().search([('master_menu', '=', 'move_out')],
                                                                    order='id DESC', limit=1)
        elif view_id == self.env.ref('empezar_move_in.move_in_tree_view').id:
            help_document_id = self.env['help.document'].sudo().search([('master_menu', '=', 'move_in')],
                                                                    order='id DESC', limit=1)
        elif view_id == self.env.ref('empezar_account_invoices.move_in_out_invoice_tree_view').id:
            help_document_id = self.env['help.document'].sudo().search([('master_menu', '=', 'move_in_out_invoice')],
                                                           order='id DESC', limit=1)
        elif view_id == self.env.ref('empezar_account_invoices.move_invoice_tree_view').id:
            help_document_id = self.env['help.document'].sudo().search([('master_menu', '=', 'invoice')],
                                                           order='id DESC', limit=1)
        elif view_id == self.env.ref('empezar_account_invoices.view_pending_invoices_tree').id:
            help_document_id = self.env['help.document'].sudo().search([('master_menu', '=', 'pending_invoice')],
                                                                    order='id DESC', limit=1)
        elif view_id ==  self.env.ref('empezar_repair.view_repair_pending_tree').id:
            help_document_id = self.env['help.document'].sudo().search([('master_menu', '=', 'repair_pending')],
                                                                    order='id DESC', limit=1)
        elif view_id == self.env.ref('empezar_repair.update_tariff_tree_view').id:
            help_document_id = self.env['help.document'].sudo().search([('master_menu', '=', 'update_tariff')],
                                                                    order='id DESC', limit=1)
        elif view_id == self.env.ref('empezar_account_invoices.monthly_lock_tree_view').id:
            help_document_id = self.env['help.document'].sudo().search([('master_menu', '=', 'monthly_lock')],
                                                                    order='id DESC', limit=1)
        elif view_id == self.env.ref('empezar_account_invoices.view_credit_note_invoice_tree').id:
            help_document_id = self.env['help.document'].sudo().search([('master_menu', '=', 'credit_note')],
                                                                    order='id DESC', limit=1)
        else:
            pass

        if help_document_id:
            attachment_obj = self.env['ir.attachment']
            attachment_id = attachment_obj.sudo().create(
                {'name': help_document_id.file_namex, 'store_fname': help_document_id.file_namex,
                 'datas': help_document_id.file,
                 'public': True})
            download_url = '/web/content/' + str(attachment_id.sudo().id) + '?download=true'
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            return {
                'name': 'File',
                'type': 'ir.actions.act_url',
                'url': str(base_url) + str(download_url),
                'target': 'new',
            }
        else:
            pass
