from odoo import http
from odoo.tests.common import get_db_name, HOST, HttpCase, new_test_user, Opener


class TestWebLoginBase(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        new_test_user(cls.env, 'Test User', context={'lang':'en_US'})

    def setUp(self):
        super().setUp()
        self.session=http.root.session_store.new()
        self.session.update(http.get_default_session(), db=get_db_name())
        self.opener=Opener(self.env.cr)
        self.opener.cookies.set('session_id', self.session.sid, domain=HOST, path='/')

    def login(self, username, password, csrf_token=None):
        res_post=self.url_open('/web/login', data={
            'login':username,
            'password':password,
            'csrf_token':csrf_token or http.Request.csrf_token(self),
        })
        res_post.raise_for_status()
        return res_post


class TestWebLogin(TestWebLoginBase):
    def test_web_login_with_valid_credentials(self):
        res_post=self.login('Test User', 'Test User')
        self.url_open(
            '/web/session/check',
            headers={'Content-Type':'application/json'},
            data='{}'
        ).raise_for_status()
        self.assertEqual(res_post.request.path_url, '/web')

    def test_web_login_with_invalid_credentials(self):
        res_post=self.login('Test User', 'test user')
        self.url_open(
            '/web/session/check',
            headers={'Content-Type':'application/json'},
            data='{}'
        ).raise_for_status()
        self.assertNotEqual(res_post.request.path_url, '/web')
