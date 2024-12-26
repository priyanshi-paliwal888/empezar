import base64
from odoo import models, fields


class ECreditNoteWizard(models.TransientModel):
    _name = 'e.invoice.credit.wizard'
    _description = 'E-Invoice  Credit Wizard'

    credit_id = fields.Many2one("credit.note.invoice", "Credit ID")
    irn_no = fields.Char(string='IRN No', required=True)
    irn_received_date = fields.Datetime(string='IRN Generated Date', required=True)
    irn_date = fields.Char()
    irn_status = fields.Selection(
        [
            ("active", "Active"),
            ("cancelled", "Cancelled"),
        ],
        string="IRN Status", store=True
    )
    generate_irn_response = fields.Text()
    invoice_ref_no = fields.Char()

    def action_download(self):
        response_content = self.generate_irn_response or ''
        file_data = base64.b64encode(response_content.encode('utf-8'))
        file_name = 'response.txt'

        # Step 2: Create or fetch an existing attachment
        attachment = self.env['ir.attachment'].create({
            'name': file_name,
            'type': 'binary',
            'datas': file_data,
            'res_model': 'e.invoice.credit.wizard',
            'res_id': self.id,
            'mimetype': 'text/plain',
        })

        # Step 3: Return the action to download the file
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
