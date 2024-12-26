from odoo import models, fields, api
import base64

class EInvoiceWizard(models.TransientModel):
    _name = 'e.invoice.wizard'
    _description = 'E-Invoice Wizard'

    invoice_id = fields.Many2one("move.in.out.invoice", "Invoice ID", store=True)
    irn_no = fields.Char(string='IRN No', required=True, store=True)
    irn_received_date = fields.Datetime(string='IRN Generated Date', required=True, store=True)
    irn_date = fields.Char()
    irn_status = fields.Selection(
        [
            ("active", "Active"),
            ("cancelled", "Cancelled"),
        ],
        string="IRN Status", store=True
    )
    generate_irn_response = fields.Text()

    def action_download(self):
        response_content = self.generate_irn_response or ''
        file_data = base64.b64encode(response_content.encode('utf-8'))
        file_name = 'generate_irn_response.txt'

        # Step 2: Create or fetch an existing attachment
        attachment = self.env['ir.attachment'].create({
            'name': file_name,
            'type': 'binary',
            'datas': file_data,
            'res_model': 'e.invoice.wizard',
            'res_id': self.id,
            'mimetype': 'text/plain',
        })

        # Step 3: Return the action to download the file
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
