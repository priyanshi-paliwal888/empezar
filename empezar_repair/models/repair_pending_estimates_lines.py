from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class RepairPendingEstimatesLines(models.Model):

    _name="repair.pending.estimates.lines"
    _description="Repair Pending Estimates Lines"

    tarrif_id = fields.Many2one('update.repair.tariff', string='Update Repair Tariff')
    estimate_id = fields.Many2one("repair.pending.estimates", string="Estimate ID", copy=False)
    description = fields.Char(string="Damage Description", required=True,size=132)
    repair_code= fields.Char(string="Repair Code", size=12)
    repair_code_id = fields.Many2one(
      'update.repair.tariff',
        string="Repair Code")
    repair_code_domain = fields.Char(string="Repair Code Domain",   compute='_compute_repair_code_domain')
    damage_location_text = fields.Char(string="Location", size=4)
    damage_location_id = fields.Many2one('update.repair.tariff', string="Location")
    damage_location= fields.Many2one('damage.locations', string="Location", size=4)
    damage_location_domain = fields.Char( string="Location Domain", compute='_compute_damage_location_domain')
    component_text = fields.Char(string="Component", size=3)
    component = fields.Many2one('master.component',string="Component", size=3)
    component_domain = fields.Char(string="Component Domain", compute='compute_component_domain')
    damage_type_text = fields.Char(string="Damage Type", size=2)
    damage_type = fields.Many2one('damage.type',string="Damage Type", size=2)
    damage_type_domain = fields.Char(string="Component Domain", compute='compute_damage_type_domain')
    repair_type_text = fields.Char(string="Repair Type", size=2)
    repair_type = fields.Many2one('repair.types',string="Repair Type", size=2)
    repair_type_domain = fields.Char(string="Repair Type Domain", compute='compute_repair_type_domain')
    material_type_text = fields.Char(string="Material", size=3)
    material_type = fields.Many2one('material.type', string="Material", size=2)
    part_no = fields.Char(string="Part No.", size=36)
    old_serial_no = fields.Char(string="Old Serial No.", size=36)
    new_serial_no = fields.Char(string="New Serial No.", size=36)
    measurement = fields.Many2one('master.uom', string="UOM", size=3)
    measurement_domain = fields.Char(string="UOM Domain", compute='compute_measurement_domain')
    key_value = fields.Many2one('key.value', string="Key Value")
    key_value_domain = fields.Char(string='Key Value Domain', compute='compute_key_value_domain')
    limit_id = fields.Many2one('update.repair.tariff',string="Limit")
    limit = fields.Many2one('repair.limit', string="Limit",  
                            help="If key value is LN then enter the length eg. 54, if key value is LN*W then enter the length and width eg. 45*67, if key value is LN*W*H then enter the length, width and height eg. 45*67*89")
    limit_domain = fields.Char(string="Limit Domain", compute='compute_limit_domain')
    limit_text = fields.Char(string="Limit", size=8)
    material_cost_tarrif_text = fields.Char(string="Material Cost(Tariff)", size=6)
    labour_hour_text = fields.Char(string="Labour Hour", size=6)
    qty = fields.Char(string="Qty")
    material_cost = fields.Integer(string="Material Cost", compute='compute_material_cost', store=True)
    labour_cost = fields.Integer(string="Labour Cost", compute='compute_labour_cost' , store=True)
    total = fields.Integer(string="Total" ,compute='compute_total_cost', store=True)
    type_size_id = fields.Many2one('container.size.type', string="Type/Size", store=True)
    is_refer = fields.Boolean(string="Is Refer", compute= "_compute_is_refer")
    repair_status = fields.Selection([
        ('awaiting_estimates', 'Awaiting Estimates'),
        ('awaiting_approval', 'Awaiting Approval'),
        ('approved', 'Approved'),
        ('partially_approved', 'Partially Approved'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected')
    ], string="Repair Status", default="awaiting_estimates")
    total_by_shipping_line = fields.Integer(string="Total By Shipping Line")
    material_cost_by_shipping_line = fields.Integer(string="Material Cost By Shipping Line")
    labour_cost_by_shipping_line = fields.Integer(string="Labour Cost By Shipping Line")
    is_qty = fields.Boolean(string="Is Qty", default=False)

    @api.depends('estimate_id')
    def _compute_is_refer(self):
        """Method to compute the is refer field."""

        for rec in self:
            if rec.estimate_id and rec.estimate_id.pending_id.type_size_id:
                rec.is_refer = rec.estimate_id.pending_id.type_size_id.is_refer == 'yes'
            else:
                rec.is_refer = False

    @api.depends('estimate_id.pending_id.type_size_id')
    def _compute_repair_code_domain(self):

        for rec in self:
            if rec.estimate_id.pending_id.type_size_id:
                size_type_code = rec.estimate_id.pending_id.type_size_id.company_size_type_code
                size_types = self.env['update.repair.tariff'].search(
                    [('size_type', '=', size_type_code)]).mapped('size_type')
                if size_types:
                    rec.repair_code_domain = [('size_type', 'in', size_types)]
                else:
                    rec.repair_code_domain = [('id', '=', False)]  # Force empty domain
            else:
                rec.repair_code_domain = [('id', '=', False)]  # Force empty domain

    @api.depends('repair_code_id', 'estimate_id.pending_id.type_size_id.company_size_type_code')
    def _compute_damage_location_domain(self):
        """Method to compute the damage location domain field."""
        for rec in self:
            if rec.repair_code_id:
                repair = self.env['update.repair.tariff'].search(
                    [('repair_code', '=', rec.repair_code_id.repair_code), ('size_type', '=',rec.estimate_id.pending_id.type_size_id.company_size_type_code)])
                rec.damage_location_domain = [('id', 'in', repair.ids)]
            else:
                size_repair = self.env['update.repair.tariff'].search([('size_type', '=',rec.estimate_id.pending_id.type_size_id.company_size_type_code)])
                rec.damage_location_domain = [('id', 'in', size_repair.ids)]

    @api.depends('damage_location_id')
    def compute_component_domain(self):
        """Method to compute the component domain field."""
        for rec in self:
            if rec.damage_location_id and rec.repair_code_id:
                damage_location = self.env['update.repair.tariff'].search([('damage_location', '=', rec.damage_location_id.damage_location),('repair_code','=',rec.repair_code_id.repair_code),('size_type','=',rec.estimate_id.pending_id.type_size_id.company_size_type_code)]).mapped('component')
                rec.component_domain = [('code', 'in', damage_location)]
            elif rec.damage_location_id: 
                damage_location = self.env['update.repair.tariff'].search([('damage_location', '=', rec.damage_location_id.damage_location),('size_type','=',rec.estimate_id.pending_id.type_size_id.company_size_type_code)]).mapped('component')
                rec.component_domain = [('code', 'in', damage_location)]
            else:
                rec.component_domain = []

    @api.depends('component')
    def compute_damage_type_domain(self):
        """Method to compute the damage type domain field."""

        for rec in self:
            if rec.component and rec.repair_code_id:
                component = self.env['update.repair.tariff'].search([('size_type','=',rec.estimate_id.pending_id.type_size_id.company_size_type_code),('component', '=', rec.component.code),('damage_location', '=', rec.damage_location_id.damage_location),('repair_code','=',rec.repair_code_id.repair_code)]).mapped('damage_type')
                rec.damage_type_domain = [('damage_type_code', 'in', component)]
            elif rec.component:
                component = self.env['update.repair.tariff'].search([('size_type','=',rec.estimate_id.pending_id.type_size_id.company_size_type_code),('component', '=', rec.component.code),('damage_location', '=', rec.damage_location_id.damage_location)]).mapped('damage_type')
                rec.damage_type_domain = [('damage_type_code', 'in', component)] 
            else:
                rec.damage_type_domain = []

    @api.depends('damage_type')
    def compute_repair_type_domain(self):
        """Method to compute the repair type domain field."""

        for rec in self:
            if rec.damage_type and rec.repair_code_id:
                damage_type = self.env['update.repair.tariff'].search([('size_type','=',rec.estimate_id.pending_id.type_size_id.company_size_type_code),('damage_type', '=', rec.damage_type.damage_type_code),('component', '=', rec.component.code),('damage_location', '=', rec.damage_location_id.damage_location),('repair_code','=',rec.repair_code_id.repair_code)]).mapped('repair_type')
                rec.repair_type_domain = [('repair_type_code', 'in', damage_type)]
            elif rec.damage_type:
                damage_type = self.env['update.repair.tariff'].search([('size_type','=',rec.estimate_id.pending_id.type_size_id.company_size_type_code),('damage_type', '=', rec.damage_type.damage_type_code),('component', '=', rec.component.code),('damage_location', '=', rec.damage_location_id.damage_location)]).mapped('repair_type')
                rec.repair_type_domain = [('repair_type_code', 'in', damage_type)]
            else:
                rec.repair_type_domain = []

    @api.depends('repair_type')
    def compute_measurement_domain(self):
        """Method to compute the measurement domain field."""

        for rec in self:
            if rec.repair_type and rec.repair_code_id:
                repair_type = self.env['update.repair.tariff'].search([('size_type','=',rec.estimate_id.pending_id.type_size_id.company_size_type_code),('repair_type','=',rec.repair_type.repair_type_code),('damage_type', '=', rec.damage_type.damage_type_code),('component', '=', rec.component.code),('damage_location', '=', rec.damage_location_id.damage_location),('repair_code','=',rec.repair_code_id.repair_code)]).mapped('measurement')
                rec.measurement_domain = [('name','in', repair_type)]
            elif rec.repair_type:
                repair_type = self.env['update.repair.tariff'].search([('size_type','=',rec.estimate_id.pending_id.type_size_id.company_size_type_code),('repair_type','=',rec.repair_type.repair_type_code),('damage_type', '=', rec.damage_type.damage_type_code),('component', '=', rec.component.code),('damage_location', '=', rec.damage_location_id.damage_location)]).mapped('measurement')
                rec.measurement_domain = [('name','in', repair_type)]    
            else:
                rec.measurement_domain = []

    @api.depends('measurement')
    def compute_key_value_domain(self):
        """Method to compute the key value domain field."""

        for rec in self:
            if rec.measurement and rec.repair_code_id:
                measurement = self.env['update.repair.tariff'].search([('size_type','=',rec.estimate_id.pending_id.type_size_id.company_size_type_code),('measurement','=',rec.measurement.name),('repair_type','=',rec.repair_type.repair_type_code),('damage_type', '=', rec.damage_type.damage_type_code),('component', '=', rec.component.code),('damage_location', '=', rec.damage_location_id.damage_location),('repair_code','=',rec.repair_code_id.repair_code)]).mapped('key_value')
                rec.key_value_domain = [('name', 'in', measurement)]
            elif rec.measurement:
                if rec.is_refer:
                    rec.key_value_domain =[]
                else:
                    measurement = self.env['update.repair.tariff'].search([('size_type','=',rec.estimate_id.pending_id.type_size_id.company_size_type_code),('measurement','=',rec.measurement.name),('repair_type','=',rec.repair_type.repair_type_code),('damage_type', '=', rec.damage_type.damage_type_code),('component', '=', rec.component.code),('damage_location', '=', rec.damage_location_id.damage_location)]).mapped('key_value')
                    rec.key_value_domain=[('name', 'in', measurement)]
            else:
                rec.key_value_domain = []

    @api.depends('key_value')
    def compute_limit_domain(self):
        """Method to compute the limit domain field."""

        for rec in self:
            if rec.key_value and rec.repair_code_id:
                key_value = self.env['update.repair.tariff'].search([('size_type','=',rec.estimate_id.pending_id.type_size_id.company_size_type_code),('key_value', '=', rec.key_value.name),('measurement','=',rec.measurement.name),('repair_type','=',rec.repair_type.repair_type_code),('damage_type', '=', rec.damage_type.damage_type_code),('component', '=', rec.component.code),('damage_location', '=', rec.damage_location_id.damage_location),('repair_code','=',rec.repair_code_id.repair_code)])
                rec.limit_domain = [('id', 'in', key_value.ids)]
            elif rec.key_value:
                key_value = self.env['update.repair.tariff'].search([('size_type','=',rec.estimate_id.pending_id.type_size_id.company_size_type_code),('key_value', '=', rec.key_value.name),('measurement','=',rec.measurement.name),('repair_type','=',rec.repair_type.repair_type_code),('damage_type', '=', rec.damage_type.damage_type_code),('component', '=', rec.component.code),('damage_location', '=', rec.damage_location_id.damage_location)])
                rec.limit_domain = [('id', 'in', key_value.ids)]
            else:
                rec.limit_domain=[]

    @api.onchange('qty', 'limit')
    def _onchange_costs(self):
        """Method to compute the material cost, labour cost and total cost."""

        for rec in self:
            rec.compute_material_cost()
            rec.compute_labour_cost()
            rec.compute_total_cost()

    @api.onchange('limit_id','limit_text')
    def compute_qty(self):
        """Method to compute the quantity."""

        for rec in self:
            if rec.measurement.name == 'QTY':
                rec.is_qty = True
                if rec.limit_id:
                    try:
                        # Safely evaluate multiplication expressions (e.g., "23*3", "34*3*3")
                        rec.qty = int(eval(rec.limit_id.limit))
                    except (SyntaxError, NameError, TypeError, ValueError):
                        # Handle invalid cases or non-multiplication strings
                        rec.qty = 0 
                if rec.limit_text:
                    try:
                        # Safely evaluate multiplication expressions (e.g., "23*3", "34*3*3")
                        rec.qty = int(eval(rec.limit_text))
                    except (SyntaxError, NameError, TypeError, ValueError):
                        # Handle invalid cases or non-multiplication strings
                        rec.qty = 0 
            else:
                continue
    @api.onchange('damage_location_id')
    def reset_fields(self):
        for rec in self:
            rec.limit_id = False   

    @api.depends('limit_id','qty','material_cost_tarrif_text')
    def compute_material_cost(self):
        """Method to compute the material cost."""

        for rec in self:
            rec.material_cost = 0
            if rec.is_refer:
                rec.material_cost = int(rec.material_cost_tarrif_text)*int(rec.qty)
            elif rec.is_refer == False:
                if rec.limit_id and rec.repair_code_id:
                    if rec.measurement.name == 'QTY':
                        limit = self.env['update.repair.tariff'].search([('size_type','=',rec.estimate_id.pending_id.type_size_id.company_size_type_code),('limit', '=', rec.limit_id.limit),('key_value', '=', rec.key_value.name),('measurement','=',rec.measurement.name),('repair_type','=',rec.repair_type.repair_type_code),('damage_type', '=', rec.damage_type.damage_type_code),('component', '=', rec.component.code),('damage_location', '=', rec.damage_location_id.damage_location),('repair_code','=',rec.repair_code_id.repair_code)], limit=1)
                        material_cost = limit.material_cost
                        rec.material_cost = material_cost
                    else:
                        limit = self.env['update.repair.tariff'].search([('size_type','=',rec.estimate_id.pending_id.type_size_id.company_size_type_code),('limit', '=', rec.limit_id.limit),('key_value', '=', rec.key_value.name),('measurement','=',rec.measurement.name),('repair_type','=',rec.repair_type.repair_type_code),('damage_type', '=', rec.damage_type.damage_type_code),('component', '=', rec.component.code),('damage_location', '=', rec.damage_location_id.damage_location),('repair_code','=',rec.repair_code_id.repair_code)], limit=1)
                        if limit:
                            material_cost = limit.material_cost
                            rec.material_cost = int(rec.qty) * material_cost
                if rec.limit_id:
                    if rec.measurement.name == 'QTY':
                        limit = self.env['update.repair.tariff'].search([('size_type','=',rec.estimate_id.pending_id.type_size_id.company_size_type_code),('limit', '=', rec.limit_id.limit),('key_value', '=', rec.key_value.name),('measurement','=',rec.measurement.name),('repair_type','=',rec.repair_type.repair_type_code),('damage_type', '=', rec.damage_type.damage_type_code),('component', '=', rec.component.code),('damage_location', '=', rec.damage_location_id.damage_location)], limit=1)
                        material_cost = limit.material_cost
                        rec.material_cost = material_cost
                    else:
                        limit = self.env['update.repair.tariff'].search([('size_type','=',rec.estimate_id.pending_id.type_size_id.company_size_type_code),('limit', '=', rec.limit_id.limit),('key_value', '=', rec.key_value.name),('measurement','=',rec.measurement.name),('repair_type','=',rec.repair_type.repair_type_code),('damage_type', '=', rec.damage_type.damage_type_code),('component', '=', rec.component.code),('damage_location', '=', rec.damage_location_id.damage_location)], limit=1)
                        if limit:
                            material_cost = limit.material_cost
                            rec.material_cost = int(rec.qty) * material_cost
            else:
                rec.material_cost = 0

    @api.depends('labour_cost','labour_hour_text')
    def compute_labour_cost(self):
        """Method to compute the labour cost."""

        for rec in self:
            rec.labour_cost = 0
            if rec.is_refer:
                shipping_lines = rec.estimate_id.pending_id.location_id.shipping_line_mapping_ids
                for mapping in shipping_lines:
                    if mapping.shipping_line_id.id == rec.estimate_id.pending_id.shipping_line_id.id:
                        labour_rate = int(mapping.labour_rate)
                        rec.labour_cost = int(rec.qty)*int(rec.labour_hour_text) * labour_rate

            elif rec.is_refer == False:
                if rec.measurement.name == 'QTY':
                    if rec.limit_id and rec.repair_code_id:
                        limit = self.env['update.repair.tariff'].search([('size_type','=',rec.estimate_id.pending_id.type_size_id.company_size_type_code),('limit', '=', rec.limit_id.limit),('key_value', '=', rec.key_value.name),('measurement','=',rec.measurement.name),('repair_type','=',rec.repair_type.repair_type_code),('damage_type', '=', rec.damage_type.damage_type_code),('component', '=', rec.component.code),('damage_location', '=', rec.damage_location_id.damage_location),('repair_code','=',rec.repair_code_id.repair_code)], limit=1)
                        if limit:
                            shipping_lines = rec.estimate_id.pending_id.location_id.shipping_line_mapping_ids
                            for mapping in shipping_lines:
                                if mapping.shipping_line_id.id == rec.estimate_id.pending_id.shipping_line_id.id:
                                    labour_rate = int(mapping.labour_rate)
                                    labour_cost_tarrif = limit.labour_hour
                                    rec.labour_cost = labour_cost_tarrif * labour_rate
                                    break
                    if rec.limit_id:
                        limit = self.env['update.repair.tariff'].search([('size_type','=',rec.estimate_id.pending_id.type_size_id.company_size_type_code),('limit', '=', rec.limit_id.limit),('key_value', '=', rec.key_value.name),('measurement','=',rec.measurement.name),('repair_type','=',rec.repair_type.repair_type_code),('damage_type', '=', rec.damage_type.damage_type_code),('component', '=', rec.component.code),('damage_location', '=', rec.damage_location_id.damage_location)], limit=1)
                        if limit:
                            shipping_lines = rec.estimate_id.pending_id.location_id.shipping_line_mapping_ids
                            for mapping in shipping_lines:
                                if mapping.shipping_line_id.id == rec.estimate_id.pending_id.shipping_line_id.id:
                                    labour_rate = int(mapping.labour_rate)
                                    labour_cost_tarrif = limit.labour_hour
                                    rec.labour_cost = labour_cost_tarrif * labour_rate
                                    break
                else:
                    if rec.limit_id and rec.repair_code_id:
                        limit = self.env['update.repair.tariff'].search([('size_type','=',rec.estimate_id.pending_id.type_size_id.company_size_type_code),('limit', '=', rec.limit_id.limit),('key_value', '=', rec.key_value.name),('measurement','=',rec.measurement.name),('repair_type','=',rec.repair_type.repair_type_code),('damage_type', '=', rec.damage_type.damage_type_code),('component', '=', rec.component.code),('damage_location', '=', rec.damage_location_id.damage_location),('repair_code','=',rec.repair_code_id.repair_code)], limit=1)
                        if limit:
                            shipping_lines = rec.estimate_id.pending_id.location_id.shipping_line_mapping_ids
                            for mapping in shipping_lines:
                                if mapping.shipping_line_id.id == rec.estimate_id.pending_id.shipping_line_id.id:
                                    labour_rate = int(mapping.labour_rate)
                                    labour_cost_tarrif = limit.labour_hour
                                    rec.labour_cost = int(rec.qty) * labour_cost_tarrif * labour_rate
                                    break
                    if rec.limit_id:
                        limit = self.env['update.repair.tariff'].search([('size_type','=',rec.estimate_id.pending_id.type_size_id.company_size_type_code),('limit', '=', rec.limit_id.limit),('key_value', '=', rec.key_value.name),('measurement','=',rec.measurement.name),('repair_type','=',rec.repair_type.repair_type_code),('damage_type', '=', rec.damage_type.damage_type_code),('component', '=', rec.component.code),('damage_location', '=', rec.damage_location_id.damage_location)], limit=1)
                        if limit:
                            shipping_lines = rec.estimate_id.pending_id.location_id.shipping_line_mapping_ids
                            for mapping in shipping_lines:
                                if mapping.shipping_line_id.id == rec.estimate_id.pending_id.shipping_line_id.id:
                                    labour_rate = int(mapping.labour_rate)
                                    labour_cost_tarrif = limit.labour_hour
                                    rec.labour_cost = int(rec.qty) * labour_cost_tarrif * labour_rate
                                    break

            else:
                rec.labour_cost = 0

    @api.depends('material_cost', 'labour_cost')
    def compute_total_cost(self):
        """Method to compute the total cost."""

        for rec in self:
            rec.total = rec.material_cost + rec.labour_cost

    @api.onchange('key_value')
    def _onchange_key_value(self):
        for rec in self:
            rec.limit_text = ''
        
    @api.constrains('qty', 'limit_text', 'material_cost_tarrif_text', 'labour_hour_text')
    @api.onchange('qty', 'limit_text', 'material_cost_tarrif_text', 'labour_hour_text')
    def _labour_rate_numeric_validation(self):
        """
       This method validates the Labour Rate entered by the user.
       Raises:
           ValidationError:
               - If the qty contains non-numeric characters.
       """
        for rec in self:
            if rec.qty:
                if not rec.qty.isdigit():
                    raise ValidationError("The Qty must contain only numeric values.")
            if rec.material_cost_tarrif_text:
                if not rec.material_cost_tarrif_text.isdigit():
                    raise ValidationError("The Material Cost(Tariff) must contain only numeric values.")
            if rec.labour_hour_text:
                if not rec.labour_hour_text.isdigit():
                    raise ValidationError("The Labour Hour must contain only numeric values.")

    @api.constrains('limit_text')
    @api.onchange('limit_text')
    def _check_numerical_input(self):
        for rec in self:
            if rec.is_refer and rec.limit_text:
                if rec.key_value.name == 'LN' :
                    if not rec.limit_text.isdigit():
                        raise ValidationError("Please enter a valid number.")
                elif rec.key_value.name == 'LN*W':
                    parts = rec.limit_text.split('*')
                    if len(parts) != 2 or not all(part.isdigit() for part in parts):
                        raise ValidationError("Please enter values in the format 'XX*YY'.")
                elif rec.key_value.name == 'LN*W*H':
                    parts = rec.limit_text.split('*')
                    if len(parts) != 3 or not all(part.isdigit() for part in parts):
                        raise ValidationError("Please enter values in the format 'XX*YY*ZZ'.")