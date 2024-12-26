# -*- coding: utf-8 -*-
# Copyright 2016 SYLEAM
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
import logging
import pdb
import requests
import werkzeug.utils
import werkzeug.wrappers
from werkzeug.wrappers import Response, response
from datetime import datetime
from odoo import http, fields
from odoo.addons.web.controllers.home import ensure_db
from odoo.http import request
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

_logger = logging.getLogger(__name__)

try:
    import oauthlib
    from oauthlib import oauth2
except ImportError:
    _logger.debug('Cannot `import oauthlib`.')


class OAuth2ProviderController(http.Controller):
    def __init__(self):
        super(OAuth2ProviderController, self).__init__()

    def _get_request_information(self):
        """ Retrieve needed arguments for oauthlib methods """
        uri = http.request.httprequest.base_url
        http_method = http.request.httprequest.method
        body = oauthlib.common.urlencode(http.request.httprequest.values.items())
        
        headers = http.request.httprequest.headers

        return uri, http_method, body, headers

    def _check_access_token(self, access_token):
        """ Check if the provided access token is valid """
        token = http.request.env['oauth.provider.token'].search([
            ('token', '=', access_token),
        ])
        if not token:
            return False

        oauth2_server = token.client_id.get_oauth2_server()
        # Retrieve needed arguments for oauthlib methods
        uri, http_method, body, headers = self._get_request_information()

        # Validate request information
        valid, oauthlib_request = oauth2_server.verify_request(
            uri, http_method=http_method, body=body, headers=headers)

        if valid:
            return token

        return False

    def _json_response(self, data=None, status=200, headers=None):
        """ Returns a json response to the client """
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        return Response(json.dumps(data), status=status, headers=headers)

    @http.route('/oauth2/authorize', type='http', auth='user', methods=['GET'], website=True)
    def authorize(self, client_id=None, response_type=None, redirect_uri=None,
                  scope=None, state=None, *args, **kwargs):
        """ Check client's request, and display an authorization page to the user,

        The authorization page lists allowed scopes
        If the client is configured to skip the authorization page, directly
        redirects to the requested URI
        """
        # data = json.loads(request.httprequest.data)
        # client_id = data['params']['client_id']
        client = http.request.env['oauth.provider.client'].search([
            ('identifier', '=', client_id),
        ])
        if not client:
            values = {
                'title': 'Unknown Client Identifier!',
                'message': 'This client identifier is invalid.',
            }
            response_data = request.render('oauth_provider.authorization_error', values)
            
            return response_data
        oauth2_server = client.get_oauth2_server()
        
        # Retrieve needed arguments for oauthlib methods
        uri, http_method, body, headers = self._get_request_information()
        try:
            scopes, credentials = oauth2_server.validate_authorization_request(uri, http_method=http_method, body=body, headers=headers)            # Store only some values, because the pickling of the full request
            # object is not possible
            
            # http.request.httpsession['oauth_scopes'] = scopes OLD Code
            # http.request.httpsession['oauth_credentials'] = { OLD Code
            parsed_url = urlparse(credentials['redirect_uri'])
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
            http.request.session['oauth_scopes'] = scopes
            http.request.session['oauth_credentials'] = {
                'client_id': credentials['client_id'],
                'redirect_uri': base_url,
                'response_type': credentials['response_type'],
                'state': credentials['state'],
            }
            if client.skip_authorization:
                # Skip the authorization page
                # Useful when the application is trusted
                return self.authorize_post()
        except oauth2.FatalClientError as e:
            values = {
                'title': 'Error: {error}'.format(error=e.error),
                'message': e.description,
            }
            response_data = request.render('oauth_provider.authorization_error', values)
            
            return response_data
        except oauth2.OAuth2Error as e:
            print("Failed to 2")
            values = {
                'title': 'Error: {error}'.format(error=e.error),
                'message': 'An unknown error occured! Please contact your administrator',
            }
            print(values)
            response_data = request.render('oauth_provider.authorization_error', values)
            
            return response_data

        oauth_scopes = client.scope_ids.filtered(
            lambda record: record.code in scopes)
        
        return http.request.render(
            'oauth_provider.authorization', {
                'oauth_client': client.name,
                'oauth_scopes': oauth_scopes,
            })

    @http.route('/oauth2/authorize', type='http', auth='user', methods=['POST'], website=True)
    def authorize_post(self, *args, **kwargs):
        """ Redirect to the requested URI during the authorization """
        client = http.request.env['oauth.provider.client'].search([
            ('identifier', '=', http.request.session.get('oauth_credentials', {}).get('client_id'))])
            # ('identifier', '=', http.request.httpsession.get('oauth_credentials', {}).get('client_id'))]) OLD Code
        if not client:
            values = {
                'title': 'Unknown Client Identifier!',
                'message': 'This client identifier is invalid.',
            }
            response_data = request.render('oauth_provider.authorization_error', values)
            return response_data
        oauth2_server = client.get_oauth2_server()

        # Retrieve needed arguments for oauthlib methods
        uri, http_method, body, headers = self._get_request_information()
        # scopes = http.request.httpsession['oauth_scopes'] Old Code
        # credentials = http.request.httpsession['oauth_credentials'] Old Code
        scopes = http.request.session['oauth_scopes']
        credentials = http.request.session['oauth_credentials']
        headers, body, status = oauth2_server.create_authorization_response(
            uri, http_method=http_method, body=body, headers=headers,
            scopes=scopes, credentials=credentials)
        
        # Custom condition add for the Empezar Procurement 
        location = headers['Location']
        old_status = status

        # Parse the URL
        parsed_url = urlparse(location)

        # Extract query parameters
        query_params = parse_qs(parsed_url.query)

        # Access specific parameters
        code = query_params.get('code', [None])[0]
        state = query_params.get('state', [None])[0]

        # Retrieve needed arguments for oauthlib methods
        uri, http_method, body, headers = self._get_request_information()
        credentials = {'scope': scopes}
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        uri = base_url + '/oauth2/access_token'

        # Retrieve the authorization code, if any, to get Odoo's user id
        existing_code = http.request.env[
            'oauth.provider.authorization.code'].search([
                ('client_id.identifier', '=', client.identifier),
                ('code', '=', code),
            ])
        if existing_code:
            credentials['odoo_user_id'] = existing_code.user_id.id
        body = {
            'client_id': http.request.session.get('oauth_credentials', {}).get('client_id'),
            # 'scope': False,
            'code': code,
            'grant_type':client.grant_type,
            'client_secret':client.secret
        }
        http_method = 'POST'
        # Access Token
        headers, body, status = oauth2_server.create_token_response(uri, http_method=http_method, body=body, headers=headers,credentials=credentials)
        body_dict = json.loads(body)
        # Add 'access_token' as the value of 'code'
        if code:
            query_params['access_token'] = body_dict.get('access_token')

        # Rebuild the query string
        new_query = urlencode(query_params, doseq=True)

         # Construct the new URL with the updated query parameters
        new_url = urlunparse(parsed_url._replace(query=new_query))
        
        return werkzeug.utils.redirect(new_url, code=old_status)

    @http.route('/oauth2/token', type='http', auth='none', methods=['POST'],csrf=False, website=True)
    def token(self, client_id=None, client_secret=None, redirect_uri=None,
              scope=None, code=None, grant_type=None, username=None,
              password=None, refresh_token=None, *args, **kwargs):
        """ Return a token corresponding to the supplied information

        Not all parameters are required, depending on the application type
        """
        # data = json.loads(request.httprequest.data)
        # client_id = data['params']['client_id']
        # code = data['params']['code'] 
        # scope = data['params']['scope']
        ensure_db()
        # If no client_id is specified, get it from session
        if client_id is None:
            # client_id = http.request.httpsession.get('oauth_credentials', {}).get('client_id') OLD Code
            client_id = http.request.session.get('oauth_credentials', {}).get('client_id')

        client = http.request.env['oauth.provider.client'].sudo().search([
            ('identifier', '=', client_id),
        ])

        if not client:
            return self._json_response(
                data={'error': 'invalid_client_id'}, status=401)
        oauth2_server = client.get_oauth2_server()

        # Retrieve needed arguments for oauthlib methods
        uri, http_method, body, headers = self._get_request_information()
        grant_type = client.grant_type
        # scope = client.scope_ids
        credentials = {'scope': scope}

        # Retrieve the authorization code, if any, to get Odoo's user id
        existing_code = http.request.env[
            'oauth.provider.authorization.code'].search([
                ('client_id.identifier', '=', client_id),
                ('code', '=', code),
            ])
        if existing_code:
            credentials['odoo_user_id'] = existing_code.user_id.id
        # Retrieve the existing token, if any, to get Odoo's user id
        existing_token = http.request.env['oauth.provider.token'].search([
            ('client_id.identifier', '=', client_id),
            ('refresh_token', '=', refresh_token),
        ])
        if existing_token:
            credentials['odoo_user_id'] = existing_token.user_id.id
        
        headers, body, status = oauth2_server.create_token_response(uri, http_method=http_method, body=body, headers=headers,credentials=credentials)
        import json
        # body = json.loads(body)
        # body['access_token'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImFkbWluQG1haWwuY29tIiwicHJvZmlsZSI6ImFkbWluIiwibmFtZSI6ImFkbWluIiwidXNlcl9pZCI6MX0.GS2iMDoRfk-nMFyMwTn1q5l_s45IXkys6ynnCzL4Q1A'
        # body = json.dumps(body)
        return Response(body, status=status, headers=headers)

    @http.route('/oauth2/access_token', type='http', auth='none', methods=['POST'],csrf=False, website=True)
    def access_token(self, client_id=None, client_secret=None, redirect_uri=None,
              scope=None, code=None, grant_type=None, username=None,
              password=None, refresh_token=None, *args, **kwargs):
        """ Return a token corresponding to the supplied information

        Not all parameters are required, depending on the application type
        """
        # data = json.loads(request.httprequest.data)
        # client_id = data['params']['client_id']
        ensure_db()
        # If no client_id is specified, get it from session
        if client_id is None:
            client_id = http.request.session.get('oauth_credentials', {}).get('client_id')

        client = http.request.env['oauth.provider.client'].sudo().search([
            ('identifier', '=', client_id),
        ])

        if not client:
            return self._json_response(
                data={'error': 'invalid_client_id'}, status=401)
        oauth2_server = client.get_oauth2_server()

        # Retrieve needed arguments for oauthlib methods
        uri, http_method, body, headers = self._get_request_information()
        credentials = {'scope': scope}

        # Retrieve the authorization code, if any, to get Odoo's user id
        existing_code = http.request.env[
            'oauth.provider.authorization.code'].search([
                ('client_id.identifier', '=', client_id),
                ('code', '=', code),
            ])
        if existing_code:
            credentials['odoo_user_id'] = existing_code.user_id.id
        # Retrieve the existing token, if any, to get Odoo's user id
        existing_token = http.request.env['oauth.provider.token'].search([
            ('client_id.identifier', '=', client_id),
            ('refresh_token', '=', refresh_token),
        ])
        if existing_token:
            credentials['odoo_user_id'] = existing_token.user_id.id
        headers, body, status = oauth2_server.create_token_response(uri, http_method=http_method, body=body, headers=headers,credentials=credentials)
        user_id = http.request.env['res.users'].sudo().search([('id', '=',existing_code.user_id.id )])   
        return Response(body, status=status, headers=headers)



    @http.route('/oauth2/tokeninfo', type='http', auth='none', methods=['GET'])
    def tokeninfo(self, access_token=None, *args, **kwargs):
        """ Return some information about the supplied token

        Similar to Google's "tokeninfo" request
        """
        ensure_db()
        token = self._check_access_token(access_token)
        if not token:
            return self._json_response(
                data={'error': 'invalid_or_expired_token'}, status=401)

        token_lifetime = (fields.Datetime.from_string(token.expires_at) -
                          datetime.now()).seconds
        # Base data to return
        data = {
            'audience': token.client_id.identifier,
            'scopes': ' '.join(token.scope_ids.mapped('code')),
            'expires_in': token_lifetime,
        }

        # Add the oauth user identifier, if user's information access is
        # allowed by the token's scopes
        user_data = token.get_data_for_model(
            'res.users', res_id=token.user_id.id)
        if 'id' in user_data:
            data.update(user_id=token.generate_user_id())
        return self._json_response(data=data)

    @http.route('/oauth2/userinfo', type='http', auth='none', methods=['GET'])
    def userinfo(self, access_token=None, *args, **kwargs):
        """ Return some information about the user linked to the supplied token

        Similar to Google's "userinfo" request
        """
        ensure_db()
        
        token = self._check_access_token(access_token)
        if not token:
            return self._json_response(data={'error': 'invalid_or_expired_token'}, status=401)

        # data = token.get_data_for_model('res.users', res_id=token.user_id.id)
        user_id = http.request.env['res.users'].sudo().search([('id', '=',token.user_id.id )])
        # user_email =  request.odoo_user.login
        
        if user_id.has_group('base.group_user'):
            user_type = 'internal'
        elif user_id.has_group('base.group_portal'):
            user_type = 'portal'
        else:
            user_type = 'public'
        data = {    
            'user_name': user_id.name,
            'user_name': user_id.login,
            'user_email': user_id.email,
            'user_id': user_id.id, 
            'user_type':user_type,
            'is_procurement_user':user_id.is_procurement_user,
            'procurement_user_type':user_id.procurement_user_type,
        }
        return self._json_response(data=data)

    @http.route('/oauth2/otherinfo', type='http', auth='none', methods=['GET'])
    def otherinfo(self, access_token=None, model=None, *args, **kwargs):
        """ Return allowed information about the requested model """
        ensure_db()
        token = self._check_access_token(access_token)
        if not token:
            return self._json_response(
                data={'error': 'invalid_or_expired_token'}, status=401)

        model_obj = http.request.env['ir.model'].search([
            ('model', '=', model),
        ])
        if not model_obj:
            return self._json_response(
                data={'error': 'invalid_model'}, status=400)

        data = token.get_data_for_model(model)
        return self._json_response(data=data)

    @http.route('/oauth2/revoke_token', type='http', auth='none', methods=['POST'])
    def revoke_token(self, token=None, *args, **kwargs):
        """ Revoke the supplied token """
        ensure_db()
        body = oauthlib.common.urlencode(
            http.request.httprequest.values.items())
        db_token = http.request.env['oauth.provider.token'].search([
            ('token', '=', token),
        ])
        if not db_token:
            db_token = http.request.env['oauth.provider.token'].search([
                ('refresh_token', '=', token),
            ])
        if not db_token:
            return self._json_response(
                data={'error': 'invalid_or_expired_token'}, status=401)
        oauth2_server = db_token.client_id.get_oauth2_server()

        # Retrieve needed arguments for oauthlib methods
        uri, http_method, body, headers = self._get_request_information()

        headers, body, status = oauth2_server.create_revocation_response(
            uri, http_method=http_method, body=body, headers=headers)
        return Response(body, status=status, headers=headers)
