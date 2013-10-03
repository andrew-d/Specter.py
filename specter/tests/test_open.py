from .util import SpecterTestCase
from .bottle import request


class TestOpen(SpecterTestCase):
    def setup_app(self, app):
        @app.route('/headers')
        def hdr():
            self.headers = request.headers
            return 'foo'

    def test_custom_headers(self):
        headers = {
            'X-Foo': 'Bar',
        }
        self.s.open(self.baseUrl + "/headers", headers=headers)
        self.s.wait_for_page_load()

        self.assert_equal(self.headers['X-Foo'], 'Bar')
