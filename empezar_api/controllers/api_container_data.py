from odoo import http
from odoo.http import request, Response
import json


class ApiController(http.Controller):

    @http.route('/fetch/container_size_type', type='http', auth='public', methods=['GET'], csrf=False)
    def list_container_size(self):
        """
            Api of container.type.data model
        """
        try:
            container_data = request.env['container.type.data'].sudo().search([('active', '=', True)])
            container_data_list = []

            if container_data:
                for container in container_data:
                    container_data_list.append({
                        'id': container.id,
                        'name': container.name,
                        'size': container.size
                    })
                return Response(json.dumps({"jsonrpc": "2.0", "id": None, 'result': container_data_list}), status=200,
                                content_type='application/json')
            else:
                error_response = {
                    'error': 'No container size types found',
                    'details': 'The search did not return any results.'
                }
                return Response(json.dumps({"jsonrpc": "2.0", "id": None, 'result': error_response}), status=400,
                                content_type='application/json')
        except Exception as e:
            error_response = {
                'error': 'An error occurred while fetching container size types',
                'details': str(e)
            }
            return Response(json.dumps({"jsonrpc": "2.0", "id": None, 'result': error_response}), status=400,
                            content_type='application/json')

    @http.route('/fetch/container_number', type='http', auth='public', methods=['GET'], csrf=False)
    def list_container_number_data(self, **kwargs):
        """
            Api of container.master model with input as container_id
        """
        try:
            container_id = kwargs.get('container_size_type_id')
            yard_id = kwargs.get('yard_id')

            if not container_id or not yard_id:
                return Response(json.dumps({'error': 'No container_type or yard parameter provided'}), status=400, content_type='application/json')

            try:
                container_data = request.env['container.inventory'].sudo().search([('container_master_id.type_size', '=', int(container_id)), ('status', '=', 'av'),('location_id', '=', int(yard_id))])
                container_data_list = []

                if container_data:
                    for container in container_data:
                        container_data_list.append({
                            'id': container.id,
                            'container_number': container.name
                        })
                    return Response(json.dumps({"jsonrpc": "2.0", "id": None,
                                                "result": container_data_list}), status=200,
                                    content_type='application/json')
                else:
                    error_response = {
                        'error': 'This container type or yard data does not have any container or available container.'
                    }
                    return Response(json.dumps(error_response), status=400, content_type='application/json')

            except Exception as e:
                error_response = {
                    'error': 'An error occurred while fetching container number',
                    'detail': str(e)
                }
                return Response(json.dumps(error_response), status=400, content_type='application/json')
        except json.JSONDecodeError as e:
            return Response(json.dumps({'error': 'Invalid JSON data'}), status=400, content_type='application/json')
        except Exception as e:
            return Response(json.dumps({'error': 'An unexpected error occurred'}), status=400, content_type='application/json')

    @http.route('/fetch/lolo_charges', type='http', auth='public', methods=['GET'], csrf=False)
    def list_lolo_charges(self,**kwargs):
        """
            Api of lolo.charge model
        """
        try:
            location = kwargs.get('location_id')
            shipping = kwargs.get('shipping_line_id')
            container_size = kwargs.get('container_size_type_id')
            operation_type = kwargs.get('operation_type')

            if not location or not shipping or not container_size or not operation_type:
                return Response(json.dumps({'error': 'No location or shipping or container size type or operation_type parameter provided'}), status=400,
                                content_type='application/json')
            try:
                lolo_charges = request.env['lolo.charge'].sudo().search(
                    [('location', '=', int(location)),('shipping_line', '=', int(shipping))], limit=1)
                container_data = request.env['container.type.data'].sudo().search([('active', '=', True),('id','=', container_size)]).mapped('size')
                lolo_charges_list = []

                if lolo_charges:
                    for lolo in lolo_charges.lolo_charge_lines:
                        lolo_container_size = dict(lolo._fields['container_size'].selection).get(lolo.container_size)
                        if lolo_container_size in container_data:
                            if operation_type == 'export':
                                field_name = 'lift_off'
                            elif operation_type == 'import':
                                field_name = 'lift_on'
                            else:
                                return Response(json.dumps({'error': 'Invalid operation type'}), status=400,
                                                content_type='application/json')    

                            charge_value = getattr(lolo, field_name)
                            lolo_charges_list.append({
                                'id': lolo.id,
                                field_name: charge_value  
                            })
                    return Response(json.dumps({"jsonrpc": "2.0", "id": None,
                                                "result": lolo_charges_list}), status=200,
                                    content_type='application/json')
                else:
                    error_response = {
                        'error': 'This location and shipping line does not have lolo charge.'
                    }
                    return Response(json.dumps(error_response), status=400, content_type='application/json')

            except Exception as e:
                error_response = {
                    'error': 'An error occurred while fetching lolo charges',
                    'detail': str(e)
                }
                return Response(json.dumps(error_response), status=400, content_type='application/json')
        except json.JSONDecodeError as e:
            return Response(json.dumps({'error': 'Invalid JSON data'}), status=400, content_type='application/json')
        except Exception as e:
            return Response(json.dumps({'error': 'An unexpected error occurred'}), status=400,
                            content_type='application/json')

    @http.route('/fetch/gst_number', type='http', auth='public', methods=['GET'], csrf=False)
    def valid_gst_number(self,**kwarg):
        """
            Api of gst_no validation model with input as gst_no
        """
        try:
            gst_no = kwarg.get('gst_no')

            if not gst_no:
                return Response(json.dumps({'error': 'No gst_no parameter provided'}), status=400,
                                content_type='application/json')
            try:
                gst_data = request.env['gst.details'].sudo().search(
                    [('gst_no', '=', gst_no)], limit=1)

                if gst_data:
                    return Response(json.dumps({"jsonrpc": "2.0", "id": None,'result': 'GSTIN is valid.'}), status=200,
                                    content_type='application/json')
                else:
                    return Response(json.dumps({"jsonrpc": "2.0", "id": None,'result': 'GSTIN is not valid'}), status=400,
                                    content_type='application/json')
            except Exception as e:
                error_response = {
                    'error': 'An error occurred while fetching gst number',
                    'detail': str(e)
                }
                return Response(json.dumps(error_response), status=400, content_type='application/json')
        except json.JSONDecodeError as e:
            return Response(json.dumps({'error': 'Invalid JSON data'}), status=400, content_type='application/json')
        except Exception as e:
            return Response(json.dumps({'error': 'An unexpected error occurred'}), status=400,
                            content_type='application/json')

    @http.route('/fetch/shipping_lines', type='http', auth='public', methods=['GET'], csrf=False)
    def list_shipping_lines(self):
        """
            Api of res.partner model for shipping lines
        """
        try:
            shipping_lines = request.env['res.partner'].sudo().search([('is_shipping_line', '=', True),('active', '=',True)])
            shipping_lines_list =[]

            if shipping_lines:
                for shipping_line in shipping_lines:
                    if shipping_line.shipping_line_name != False:
                        shipping_lines_list.append({
                            'id': shipping_line.id,
                            'name': shipping_line.shipping_line_name,
                            'code': shipping_line.shipping_line_code
                        })
                return  Response(json.dumps({"jsonrpc": "2.0", "id": None, 'result': shipping_lines_list}), status=200,
                                content_type='application/json')
            else:
                error_response = {
                    'error': 'No Shipping Lines found',
                    'details': 'The search did not return any results.'
                }
                return Response(json.dumps({"jsonrpc": "2.0", "id": None, 'result': error_response}), status=400,
                                content_type='application/json')
        except Exception as e:
            error_response = {
                        'error': 'An error occurred while fetching Shipping Lines',
                        'details': str(e)
            }
            return Response(json.dumps({"jsonrpc": "2.0", "id": None, 'result': error_response}), status=400,
                                    content_type='application/json')

    @http.route('/fetch/yard', type='http', auth='public', methods=['GET'], csrf=False)
    def list_yard(self):
        """
            Api of res.company model for location
        """
        try:
            locations = request.env['res.company'].sudo().search([('parent_id','!=',False),('active', '=',True)])
            location_list = []

            if locations:
                for location in locations:
                    location_list.append({
                        'id': location.id,
                        'location_name': location.name,
                        'address_line_1': location.street,
                        'address_line_2': location.street2,
                        'city': location.city,
                        'state': location.state_id.name,
                        'country': location.country_id.name,
                        'pin_code': location.zip,
                        'email': location.email,
                        'escalation_email_ids': location.escalation_email,
                        'contact_no': location.phone,
                        'gst_no': location.gst_no
                    })

                return Response(json.dumps({"jsonrpc": "2.0", "id": None, 'result': location_list}), status=200,
                                content_type='application/json')
            else:
                error_response = {
                    'error': 'No Location found',
                    'details': 'The search did not return any results.'
                }
                return Response(json.dumps({"jsonrpc": "2.0", "id": None, 'result': error_response}), status=400,
                                content_type='application/json')
        except Exception as e:
            error_response = {
                'error': 'An error occurred while fetching Location',
                'details': str(e)
            }
            return Response(json.dumps({"jsonrpc": "2.0", "id": None, 'result': error_response}), status=400,
                            content_type='application/json')
        
    @http.route('/get/lolo_charges', type='http', auth='public', methods=['GET'], csrf=False)
    def get_lolo_charges(self, **kwargs):
        """
            API for lolo.charge model to return all records with specified format.
        """
        try:
            lolo_charges = request.env['lolo.charge'].sudo().search([('active', '=',True)])
            response_data = []

            for lolo in lolo_charges:
                location_id = lolo.location.id
                shipping_line_id = lolo.shipping_line.id

                charges_lines = []
                for lolo_line in lolo.lolo_charge_lines:
                    container_size = dict(lolo_line._fields['container_size'].selection).get(lolo_line.container_size)
                    
                    charge_data = {
                        'container': container_size,
                        'lifton': lolo_line.lift_on if lolo_line.lift_on else 0 ,
                        'liftoff': lolo_line.lift_off if lolo_line.lift_off else 0,
                    }
                    
                    charges_lines.append(charge_data)
                
                response_data.append({
                    'location_id': location_id,
                    'shipping_line_id': shipping_line_id,
                    'charges_lines': charges_lines

                })

            return Response(json.dumps({"jsonrpc": "2.0", "id": None, "result": response_data}), status=200, content_type='application/json')
        
        except Exception as e:
            return Response(json.dumps({'error': str(e)}), status=500, content_type='application/json')

    @http.route('/get/container_data_list', type='http', auth='public', methods=['GET'], csrf=False)
    def get_container_data_list(self, **kwargs):
        """
        API endpoint to return all container.master records with specific fields.
        :return: HTTP response with container.master records
        """
        try:
            container_inventory = request.env['container.inventory'].sudo().search([('status', '=', 'av')])
            # Check if no active containers are found
            if not container_inventory:
                return Response(json.dumps({
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": 404, "message": "No active container found"}
                }), status=404, content_type='application/json')

            result = []

            for record in container_inventory:
                get_shipping_line_id = ''
                get_type_size_id = ''
                if record.container_master_id:
                    get_shipping_line_id = record.container_master_id.shipping_line_id.id
                    get_type_size_id = record.container_master_id.type_size.id
                result.append({
                    'name': record.name,
                    'yard_id': record.location_id.id,
                    'shipping_line_id': get_shipping_line_id,
                    'type_size_id': get_type_size_id
                })

            return Response(json.dumps({"jsonrpc": "2.0", "id": None, "result": result}), status=200,
                            content_type='application/json')
        except Exception as e:
            return Response(json.dumps({'error': str(e)}), status=500, content_type='application/json')
    
