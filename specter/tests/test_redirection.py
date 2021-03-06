from .util import SpecterTestCase
from .bottle import redirect


class TestRedirection(SpecterTestCase):
    def setup_app(self, app):
        @app.route('/one')
        def one():
            return b'url one'

        @app.route('/two/<code:int>')
        def two(code):
            return redirect('/one', code)

    def test_working(self):
        self.open('/two/303')
        self.assert_equal(self.s.url, self.baseUrl + '/one')
        self.assert_equal(self.s.requested_url, self.baseUrl + '/two/303')
