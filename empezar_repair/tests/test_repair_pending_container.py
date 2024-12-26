from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError
from lxml import etree

class TestRepairPendingContainerModel(TransactionCase):

    def setUp(self):
        super().setUp()

        self.repair_pending_model = self.env['repair.pending']
        self.container_type_size = self.env["container.type.data"].create(
            {
                "name": "20FT",
                "company_size_type_code": "20FT",
                "is_refer": "yes",
            }
        )

        self.shipping_line = self.env['res.partner'].create({
            'name': 'Test Shipping Line',
            'shipping_line_name': 'Test Shipping Line',
            'is_shipping_line': True,
            'applied_for_interchange': 'yes'
        })

        self.damage_condition = self.env["damage.condition"].create(
            {"name": "Damage A", "damage_code": "Size/Type A", "active": True}
        )

        self.container_master = self.env["container.master"].create(
            {
                "name": "GVTU3000389",
                "type_size": self.container_type_size.id,
                "shipping_line_id": self.shipping_line.id,
                "gross_wt": "350",
                "tare_wt": "123",
                "year": "1952",
                "month": "10",
            }
        )

        self.location_shipping_line = self.env["location.shipping.line.mapping"].create(
            {
                "shipping_line_id": self.shipping_line.id,
                "company_id": self.env.company.id,
                "refer_container": "yes",
                "repair": "yes"
            }
        )

        self.location = self.env["res.company"].create(
            {
                "name": "Test Location A",
                "street": "Test Location",
                "active": True,
            }
        )

        self.location_with_repair = self.env['res.company'].create({
            "name": "Test Location B",
            "operations_ids": [(6, 0, [2])],
            "active": True,
            "shipping_line_mapping_ids": [(6, 0, [self.location_shipping_line.id])],
        })

        self.move_in = self.env["move.in"].create(
            {
                "container": "GVTU3000389",
                "location_id": self.location_with_repair.id,
                "mode": "truck",
                "shipping_line_id": self.shipping_line.id,
                "type_size_id": self.container_type_size.id,
                "grade": "a",
                "damage_condition": self.damage_condition.id,
            }
        )

        self.repair_pending_container = self.repair_pending_model.create({
            'location_id': self.location_with_repair.id,
            'shipping_line_id': self.shipping_line.id,
            'container_no': 'GVTU3000389',
            'grade': 'a',
            'damage_condition': self.damage_condition.id,
            "type_size_id": self.container_type_size.id,
            'gross_wt': 300,
            'tare_wt': 50,
        })

        self.existing_estimate = self.env['repair.pending.estimates'].create({
            'pending_id': self.repair_pending_container.id,
        })

    def test_get_years(self):

        years = self.repair_pending_container.get_years()
        self.assertEqual(years[1], ('1951', '1951'))

    def test_onchange_container_no_existing(self):

        self.repair_pending_container._onchange_container_no()
        self.assertEqual(self.repair_pending_container.shipping_line_id, self.container_master.shipping_line_id)
        self.assertEqual(self.repair_pending_container.type_size_id, self.container_master.type_size)
        self.assertEqual(self.repair_pending_container.gross_wt, self.container_master.gross_wt)
        self.assertEqual(self.repair_pending_container.tare_wt, self.container_master.tare_wt)
        self.assertEqual(self.repair_pending_container.year, self.container_master.year)
        self.assertEqual(self.repair_pending_container.month, self.container_master.month)

    def test_onchange_container_no_non_existing(self):

        self.repair_pending_container.container_no = 'CING0000022'
        self.repair_pending_container._onchange_container_no()
        self.assertFalse(self.repair_pending_container.shipping_line_id)
        self.assertFalse(self.repair_pending_container.type_size_id)
        self.assertFalse(self.repair_pending_container.gross_wt)
        self.assertFalse(self.repair_pending_container.tare_wt)
        self.assertFalse(self.repair_pending_container.year)
        self.assertFalse(self.repair_pending_container.month)

    def test_compute_location_id_domain_with_repair(self):
        self.repair_pending_container._compute_location_id_domain()
        """Check the computed domain when the operation type is 'repair'."""
        expected_domain = str([('id', 'in', [self.location_with_repair.id])])
        self.assertEqual(self.repair_pending_container.location_id_domain, expected_domain)

    def test_compute_shipping_line_id_domain_with_location(self):
        self.repair_pending_container._compute_shipping_line_id_domain()

        expected_domain = self.shipping_line
        self.assertEqual(self.repair_pending_container.shipping_line_id_domain, expected_domain)

    def test_compute_shipping_line_id_domain_without_location(self):
        """ Set location_id to False """

        self.repair_pending_container.location_id = False

        self.repair_pending_container._compute_shipping_line_id_domain()

        self.assertEqual(self.repair_pending_container.shipping_line_id_domain.id, False)

    def test_compute_display_name_with_type_size_code(self):
        self.repair_pending_container._compute_display_name()

        expected_display_name = f'{self.container_master.name}({self.container_type_size.company_size_type_code})'
        self.assertEqual(self.repair_pending_container.display_name, expected_display_name)

    def test_compute_display_name_without_type_size_code(self):
        """ Create a type size without a company size type code """
        type_size_no_code = self.env['container.type.data'].create({
            'name': 'Small',
            'company_size_type_code': False
        })

        container_new = self.env['container.master'].create({
            'name': 'FEDT9106732',
            'type_size': type_size_no_code.id
        })

        """ Set the container_no to the new container """
        self.repair_pending_container.container_no = container_new.name

        self.repair_pending_container._compute_display_name()

        """Check that the display name is set to the container name"""
        self.assertEqual(self.repair_pending_container.display_name, container_new.name)

    def test_valid_container_no(self):
        """Check when Container no. is valid"""
        self.repair_pending_container._check_container_no_validations()

    def test_invalid_length_container_no(self):
        """ Set an invalid container number (length not 11) """

        with self.assertRaises(ValidationError):
            self.repair_pending_container.container_no = 'ABC12345'
            self.repair_pending_container._check_container_no_validations()

    def test_invalid_format_container_no(self):
        """ Set an invalid container number (wrong format) """

        with self.assertRaises(ValidationError):
            self.repair_pending_container.container_no = 'ABCD123452X'
            self.repair_pending_container._check_container_no_validations()


    def test_invalid_check_digit(self):
        """ Set a valid length and format but invalid check digit """

        with self.assertRaises(ValidationError):
            self.repair_pending_container.container_no = 'ABCD1234565'
            self.repair_pending_container._check_container_no_validations()

    def test_refer_container_not_allowed(self):
        """ Change the mapping to allow reefer containers """

        self.repair_pending_container.location_id.shipping_line_mapping_ids.refer_container = 'no'

        with self.assertRaises(ValidationError) as e:
            self.repair_pending_container._check_container_no_validations()
        self.assertEqual(str(e.exception), "No reefer containers are allowed ")

    def test_type_size_not_refer(self):
        self.repair_pending_container.type_size_id.is_refer = 'no'
        with self.assertRaises(ValidationError) as e:
            self.repair_pending_container._check_container_no_validations()
        self.assertEqual(str(e.exception), "No reefer containers are allowed ")

    def test_action_add_estimate(self):
        """ Test action_add_estimate when an existing estimate is found """
        result = self.repair_pending_container.action_add_estimate()
        self.assertEqual(result['type'], 'ir.actions.act_window')
        self.assertEqual(result['res_model'], 'repair.pending.estimates')
        self.assertEqual(result['res_id'], self.existing_estimate.id)
        self.assertEqual(result['name'], 'Estimate Form')

    def test_action_add_estimate_no_existing(self):
        """ Test action_add_estimate when no existing estimate is found """
        self.existing_estimate.unlink()
        result = self.repair_pending_container.action_add_estimate()
        self.assertEqual(result['type'], 'ir.actions.act_window')
        self.assertEqual(result['res_model'], 'repair.pending.estimates')
        self.assertNotIn('res_id', result)
        self.assertEqual(result['context'], {'default_pending_id': self.repair_pending_container.id})
        self.assertEqual(result['name'], 'Estimate Form')

    def test_action_edit_estimate(self):
        self.repair_pending_container.action_edit_estimate()

    def test_action_view_estimate(self):
        self.repair_pending_container.action_view_estimate()

    def test_action_repair_completion(self):
        self.repair_pending_container.action_repair_completion()

    def test_get_view_multiple_companies(self):
        """ Test get_view when the user has multiple companies """
        """ Create a mock view response """
        mock_view_id = self.env.ref('empezar_repair.view_repair_pending_tree')
        res = self.env['repair.pending'].get_view(mock_view_id.id, 'tree')

        """ Assertions to check that the response is unchanged """
        self.assertIn('arch', res, "Response should contain 'arch'.")
        self.assertNotIn('create', res['arch'], "Create should not be set to false.")

    def test_get_view_single_company_with_repair_operations(self):
        """ Test get_view when the user has a single company with 'Repair' operation """
        self.env.user.company_id = self.location_with_repair

        """ Create a mock view response """
        mock_view_id = self.env.ref('empezar_repair.view_repair_pending_tree')
        res = self.env['repair.pending'].get_view(mock_view_id.id, 'tree')

        """ Assertions to check that the response has 'create' set to 'false' """
        self.assertIn('arch', res, "Response should contain 'arch'.")
        doc = etree.XML(res['arch'])
        tree_node = doc.xpath("//tree")[0]
        self.assertEqual(tree_node.get('create'), None, "Create should be set to 'false'.")

    def test_get_view_single_company_without_repair_operations(self):
        """ Test get_view when the user has a single company without 'Repair' operation """
        self.env.user.company_id = self.location
        
        """ Create a mock view response """
        mock_view_id = self.env.ref('empezar_repair.view_repair_pending_tree')
        res = self.env['repair.pending'].get_view(mock_view_id.id, 'tree')

        """ Assertions to check that the response is unchanged """
        self.assertIn('arch', res, "Response should contain 'arch'.")
        doc = etree.XML(res['arch'])
        tree_node = doc.xpath("//tree")[0]
        self.assertNotIn('create', tree_node.attrib, "Create should not be set to 'false'.")




