from odoo.tests.common import TransactionCase

class TestContainerFacilities(TransactionCase):

    def setUp(self):
        super(TestContainerFacilities, self).setUp()
        # Create a dummy port for context
        self.port = self.env['res.partner'].create({
            'name': 'Test Port',
        })

    def test_default_get_is_from_cfs_icd(self):
        """Test default_get with context 'is_from_cfs_icd'."""
        context = {'is_from_move_out': True, 'is_from_cfs_icd': True}
        defaults = self.env['container.facilities'].with_context(context).default_get(['facility_type', 'port'])
        self.assertEqual(defaults['facility_type'], 'cfs')
        self.assertFalse(defaults['port'])

    def test_default_get_is_from_terminal(self):
        """Test default_get with context 'is_from_terminal'."""
        context = {'is_from_move_out': True, 'is_from_terminal': True, 'port': self.port.id}
        defaults = self.env['container.facilities'].with_context(context).default_get(['facility_type', 'port'])
        self.assertEqual(defaults['facility_type'], 'terminal')
        self.assertEqual(defaults['port'], self.port.id)
    #
    def test_default_get_is_from_empty_yard(self):
        """Test default_get with context 'is_from_empty_yard'."""
        context = {'is_from_move_out': True, 'is_from_empty_yard': True}

        defaults = self.env['container.facilities'].with_context(context).default_get(['facility_type', 'port'])
        self.assertEqual(defaults['facility_type'], 'empty_yard')
        self.assertFalse(defaults['port'])
