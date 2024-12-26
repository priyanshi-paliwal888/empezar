from odoo.tests import common
from odoo.exceptions import ValidationError

class TestSecurityPolicy(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.security_policy_model = self.env['security.policy']

    def test_create_security_policy_valid_ip_address(self):
        """Test that a valid IP address passes validation."""
        self.security_policy_model.create({
            'name': 'Test Policy',
            'ip_address': '192.168.1.100',
            'access': 'allow',
        })

    def test_create_security_policy_invalid_ip_address(self):
        """Test that an invalid IP address raises a ValidationError."""
        with self.assertRaises(ValidationError) as e:
            self.security_policy_model.create({
                'name': 'Test Policy',
                'ip_address': 'invalid_ip',
                'access': 'allow',
            })
        self.assertEqual(e.exception.args[0], 'Ip Address entered is invalid. kindly enter valid IP Address')

    def test_create_security_policy_invalid_ip_format(self):
        """Test that an IP address with invalid format raises a ValidationError."""
        with self.assertRaises(ValidationError) as e:
            self.security_policy_model.create({
                    'name': 'Test Policy',
                    'ip_address': '192.168.1.256',
                    'access': 'allow',
                })
        self.assertEqual(e.exception.args[0], 'Ip Address entered is invalid. kindly enter valid IP Address')
