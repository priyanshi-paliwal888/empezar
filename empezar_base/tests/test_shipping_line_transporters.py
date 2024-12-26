from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestShippingLineTransporters(TransactionCase):

    def setUp(self):
        super(TestShippingLineTransporters, self).setUp()
        self.transporter_model=self.env['shipping.line.transporters']
        self.partner_model=self.env['res.partner']

    def test_create_transporter(self):
        transporter_data={
            'transporter_id':self.partner_model.create({'name':'Test Transporter'}).id,
            'code':'T001',
            'active':True
        }
        transporter=self.transporter_model.create(transporter_data)
        self.assertTrue(transporter)

    def test_deactivate_transporter(self):
        transporter=self.transporter_model.create({
            'transporter_id':self.partner_model.create({'name':'Test Transporter'}).id,
            'code':'T001',
            'active':True
        })
        transporter.active=False
        self.assertFalse(transporter.active)
        self.assertEqual(transporter.rec_status, 'disable')

    def test_duplicate_code(self):
        partner_1=self.partner_model.create({'name':'Transporter 1'})
        partner_2=self.partner_model.create({'name':'Transporter 2'})

        transporter_1=self.transporter_model.create({
            'transporter_id':partner_1.id,
            'code':'T001',
            'active':True
        })

        with self.assertRaises(ValidationError):
            self.transporter_model.create({
                'transporter_id':partner_2.id,
                'code':'T001',
                'active':True
            })

    def test_duplicate_transporter_name(self):
        partner=self.partner_model.create({'name':'Common Partner'})

        transporter_1=self.transporter_model.create({
            'transporter_id':partner.id,
            'code':'T001',
            'active':True
        })

        with self.assertRaises(ValidationError):
            self.transporter_model.create({
                'transporter_id':partner.id,
                'code':'T002',
                'active':True
            })

    def test_rec_status_computation(self):
        transporter=self.transporter_model.create({
            'transporter_id':self.partner_model.create({'name':'Test Transporter'}).id,
            'code':'T003',
            'active':True
        })

        self.assertEqual(transporter.rec_status, 'active')

        transporter.active=False
        transporter._check_active_records()
        self.assertEqual(transporter.rec_status, 'disable')

    def test_create_record_info(self):
        self.env.user.tz = 'UTC'
        transporter=self.transporter_model.create({
            'transporter_id':self.partner_model.create({'name':'Test Transporter'}).id,
            'code':'T004',
            'active':True
        })

        transporter._get_create_record_info()
        self.assertTrue(transporter.display_create_info)
    #
    def test_modify_record_info(self):
        self.env.user.tz='UTC'
        transporter=self.transporter_model.create({
            'transporter_id':self.partner_model.create({'name':'Test Transporter'}).id,
            'code':'T005',
            'active':True
        })

        transporter._get_modify_record_info()
        self.assertTrue(transporter.display_modified_info)
