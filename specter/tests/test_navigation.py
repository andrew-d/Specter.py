import os

from .util import SpecterTestCase
from .bottle import static_file


class TestSimple(SpecterTestCase):
    STATIC_FILE = 'nav1.html'

    def setupApp(self, app):
        root = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'static'
        )
        self.served = 0

        @app.route('/<path:path>')
        def rest(path):
            print("Serving static file: %s" % (path,))
            self.served += 1
            return static_file(filename=path, root=root)

    def test_go_back(self):
        self.open('/nav1.html')
        self.open('/nav2.html')
        self.assert_true(self.s.url.endswith('/nav2.html'))

        self.s.go_back()
        self.s.wait_for_page_load()

        self.assert_true(self.s.url.endswith('/nav1.html'))

    def test_go_forward(self):
        self.open('/nav1.html')
        self.open('/nav2.html')
        self.open('/nav3.html')

        self.s.go_back()
        self.s.wait_for_page_load()
        self.assert_true(self.s.url.endswith('/nav2.html'))

        self.s.go_forward()
        self.s.wait_for_page_load()
        self.assert_true(self.s.url.endswith('/nav3.html'))

    def test_reload(self):
        self.open('/nav1.html')
        self.assert_equal(self.served, 1)

        self.s.reload()
        self.s.wait_for_page_load()
        self.assert_equal(self.served, 2)

    def test_stop(self):
        self.open('/nav1.html')
        self.assert_equal(self.served, 1)

        self.s.reload()
        self.s.stop()
        self.s.wait_for_page_load()
        # TODO: assert something?
