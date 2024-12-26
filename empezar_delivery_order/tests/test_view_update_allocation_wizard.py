from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class TestContainerDetailsWizard(TransactionCase):

    def setUp(self):
        super(TestContainerDetailsWizard, self).setUp()

        # Create test data
        self.delivery_order_model = self.env['delivery.order']
        self.container_details_model = self.env['container.details.delivery']
        self.container_details_wizard_model = self.env['view.update.allocation.wizard']
        self.res_company_model = self.env['res.company']
        self.container_type_model = self.env['container.type.data']

        self.company = self.res_company_model.create({'name': 'Test Company', 'location_type': 'empty_yard'})
        self.container_type = self.container_type_model.create({'name': '20ft', 'is_refer': 'yes'})
        self.container_type_02 = self.container_type_model.create({'name': '200ft', 'is_refer': 'yes'})
        # Load or create necessary records
        self.shipping_line = self.env['res.partner'].create({
            'name': 'Test Shipping Line',
            'is_shipping_line': True,
            'active': True
        })
        self.master_port_data_model = self.env['master.port.data']
        # Create a port for loading
        self.port_loading = self.master_port_data_model.create({
            'country_iso_code': 'US',
            'port_code': 'TESTPORT',
            'port_name': 'Test Port',
            'state_code': 'NY',
            'status': 'Active',
            'latitude': '40.7128° N',
            'longitude': '74.0060° W',
            'popular_port': True,
            'active': True,
        })
        # Create a port for discharge
        self.port_discharge = self.master_port_data_model.create({
            'country_iso_code': 'US',
            'port_code': 'TESTPORT',
            'port_name': 'Test Port',
            'state_code': 'NY',
            'status': 'Active',
            'latitude': '40.7128° N',
            'longitude': '74.0060° W',
            'popular_port': True,
            'active': True,
        })

        self.master_port_data_model = self.env["master.port.data"]
        # Create a master port data for testing
        self.port = self.master_port_data_model.create(
            {
                "country_iso_code": "US",
                "port_code": "TESTPORT",
                "port_name": "Test Port",
                "state_code": "NY",
                "status": "Active",
                "latitude": "40.7128° N",
                "longitude": "74.0060° W",
                "popular_port": True,
                "active": True,
            }
        )

        facility_data = {
            "name": "Test Facility",
            "facility_type": "empty_yard",
            "code": "TF001",
            "port": self.port.id,
            "active": True,
        }
        facility = self.env['container.facilities'].create(facility_data)

        self.location = self.env['res.company'].create({'name': 'Test Location', 'active': True})
        self.container_details = self.env['container.details.delivery'].create({
            'delivery_id': False,  # Will be set after creating the delivery order
            'container_qty': 10,
            'balance_container': 5,
            'container_size_type': self.env['container.type.data'].create({'name': '20ft', 'is_refer': 'yes'}).id,
            'container_yard': facility.id
        })
        self.delivery_order = self.env['delivery.order'].create({
            'delivery_no': 'DO151',
            'shipping_line_id': self.shipping_line.id,
            'delivery_date': datetime.today().date(),
            'validity_datetime': datetime.today() + timedelta(days=1),
            'exporter_name': self.env['res.partner'].create({'name': 'Test Exporter'}).id,
            'booking_party': self.env['res.partner'].create({'name': 'Test Booking Party'}).id,
            'forwarder_name': self.env['res.partner'].create({'name': 'Test Forwarder'}).id,
            'import_name': self.env['res.partner'].create({'name': 'Test Importer'}).id,
            'commodity': 'Test Commodity',
            'cargo_weight': '1000',
            'vessel': 'Test Vessel',
            'voyage': 'Test Voyage',
            'remark': 'Test Remark',
            'port_loading': self.port_loading.id,
            'port_discharge': self.port_discharge.id,
            'location': [(6, 0, [self.location.id])],
            'to_from_location': self.location.id,
            'stuffing_location': self.location.id,
            'total_containers': 10,
            'balance_containers': 5,
            'container_details': [(6, 0, [self.container_details.id])]
        })
        self.container_detail_1 = self.container_details_model.create({
            'delivery_id': self.delivery_order.id,
            'container_qty': 10,
            'container_size_type': self.container_type.id,
        })
        self.container_detail_2 = self.container_details_model.create({
            'delivery_id': self.delivery_order.id,
            'container_qty': 20,
            'container_size_type': self.container_type_02.id,
        })

    def test_action_update_allocation_success(self):
        """Test successful update of container details with valid quantities."""
        wizard = self.container_details_wizard_model.create({
            'delivery_order_id': self.delivery_order.id,
            'container_details': [(6, 0, [self.container_detail_1.id, self.container_detail_2.id])],
        })
        # Update container_qty
        self.container_detail_1.container_qty = 10
        self.container_detail_2.container_qty = 20

        # Update quantities
        self.container_detail_1.quantity = 20
        self.container_detail_2.quantity = 50
        """Test that the quantity is bigger then container_qty"""
        with self.assertRaises(ValidationError):
            wizard.action_update_allocation()

        # Update quantities
        self.container_detail_1.quantity = 5
        self.container_detail_2.quantity = 15
        """Test that the quantity is less then container_qty"""
        wizard.action_update_allocation()
        # Check if balance_container is updated correctly
        self.assertEqual(self.container_detail_1.balance_container, 5)
        self.assertEqual(self.container_detail_2.balance_container, 5)

    def test_action_update_allocation_exceed_quantity(self):
        """Test action_update_allocation raises ValidationError when quantity exceeds container_qty."""
        wizard = self.container_details_wizard_model.create({
            'delivery_order_id': self.delivery_order.id,
            'container_details': [(6, 0, [self.container_detail_1.id])],
        })

        # Set quantity greater than container_qty
        self.container_detail_1.quantity = 60

        with self.assertRaises(ValidationError):
            wizard.action_update_allocation()

    def test_action_update_allocation_no_quantity(self):
        """Test action_update_allocation works when quantity is not set."""
        wizard = self.container_details_wizard_model.create({
            'delivery_order_id': self.delivery_order.id,
            'container_details': [(6, 0, [self.container_detail_1.id])],
        })
        # Update container_qty
        self.container_detail_1.container_qty = 50
        # Set quantity to None
        self.container_detail_1.quantity = None

        wizard.action_update_allocation()

        # Check if balance_container is not updated
        self.assertEqual(self.container_detail_1.balance_container, 10)

    def test_action_update_allocation_no_container_details(self):
        """Test action_update_allocation when no container details are provided."""
        wizard = self.container_details_wizard_model.create({
            'delivery_order_id': self.delivery_order.id,
            # 'container_details': [(6, 0, [self.container_detail_1.id])],
        })

        # Update allocation without any container details
        wizard.action_update_allocation()

        # No container details should be updated or modified
        # This is a no-op, but ensures no errors are raised.
