from odoo.tests.common import TransactionCase

class TestMovementSetting(TransactionCase):

    def setUp(self):
        super(TestMovementSetting, self).setUp()
        self.movement_setting_model = self.env['movement.setting']
        self.company_model = self.env['res.company']

        # Create a company for the test
        self.company = self.company_model.create({'name': 'Test Company'})

        # Use an existing field for the test (e.g., name field of res.partner model)
        self.field_name = self.env['ir.model.fields'].search([('name', '=', 'name'), ('model', '=', 'res.partner')], limit=1)

    def test_create_movement_setting(self):
        """ Test creation of MovementSetting with valid data """
        movement_setting = self.movement_setting_model.create({
            'field_name': self.field_name.id,
            'show_on_screen': True,
            'mandatory': 'yes',
            'company_id': self.company.id,
            'movement_type': 'move_in'
        })
        self.assertTrue(movement_setting)
        self.assertEqual(movement_setting.mandatory, 'yes')

    def test_onchange_show_on_screen(self):
        """ Test the onchange_show_on_screen method """
        movement_setting = self.movement_setting_model.new({
            'show_on_screen': False
        })
        # Initially mandatory should be 'no'
        movement_setting.onchange_show_on_screen()
        self.assertEqual(movement_setting.mandatory, 'no')

        # Change show_on_screen to True
        movement_setting.show_on_screen = True
        movement_setting.onchange_show_on_screen()
        self.assertEqual(movement_setting.mandatory, 'yes')

        # Change show_on_screen back to False
        movement_setting.show_on_screen = False
        movement_setting.onchange_show_on_screen()
        self.assertEqual(movement_setting.mandatory, 'no')

    def test_create_with_context(self):
        """ Test creating MovementSetting with context-based default_movement_type """
        # Using the with_context method to set the context for testing
        movement_setting = self.movement_setting_model.with_context(default_movement_type='move_out').create({
            'field_name': self.field_name.id,
            'show_on_screen': False,
            'mandatory': 'no',
            'company_id': self.company.id
        })
        self.assertTrue(movement_setting)
        self.assertEqual(movement_setting.movement_type, 'move_out')
