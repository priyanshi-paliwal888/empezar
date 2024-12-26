from odoo.tests import common
from odoo.exceptions import ValidationError

class TestUnlinkContainerWizard(common.TransactionCase):

    def setUp(self):
        super(TestUnlinkContainerWizard, self).setUp()

        # Create a dummy unlink reason and container numbers
        self.unlink_reason = self.env['unlink.reason'].create({
            'reason': 'Damaged'
        })

        self.container_number1 = self.env['container.number'].create({
            'name': 'GVTU3000389',
            'unlink_reason': False,
            'is_unlink': False,
            'is_unlink_non_editable': False
        })

    def test_default_get(self):
        """
        Test that the wizard fetches default container_ids from context
        """
        context = {'container_ids': [self.container_number1.id]}
        wizard = self.env['unlink.container.wizard'].with_context(context).create({})
        self.assertIn(self.container_number1, wizard.container_ids)

    def test_unlink_containers(self):
        """
        Test the unlink_containers method for redirecting to confirmation wizard with the correct context.
        """
        wizard = self.env['unlink.container.wizard'].create({
            'container_ids': [(6, 0, [self.container_number1.id])],
            'unlink_reason': self.unlink_reason.id
        })

        action = wizard.unlink_containers()

        # Verify action properties
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'unlink.container.confirmation')
        self.assertEqual(action['view_mode'], 'form')
        self.assertEqual(action['target'], 'new')

        # Verify context passed to the confirmation window
        self.assertEqual(action['context']['default_container_ids'], [self.container_number1.id])
        self.assertEqual(action['context']['default_unlink_reason'], self.unlink_reason.id)
