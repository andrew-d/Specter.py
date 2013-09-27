import unittest

from util import SpecterTestCase


class TestSimpleOpening(SpecterTestCase):
    def setupApp(self, app):
        @app.route('/')
        def index():
            return b'''
                <html>
                    <head><title>This is a title</title></head>
                    <body>This is an index page</body>
                </html>
            '''

        @app.route('/a_distinct_url')
        def dis():
            return b'distinct'

    def test_simple_and_sleep(self):
        self.open('/')
        #self.s.sleep(0.5)
        self.s.wait_for_page_load()
        self.assertTrue('This is an index page' in self.s.content)

    def test_wait_for(self):
        self.open('/')
        self.s.wait_for(lambda: 'This is an index page' in self.s.content)

    def test_url(self):
        self.open('/a_distinct_url')
        self.s.wait_for_page_load()
        self.assertEqual(self.s.url,
                         'http://%s:%d/a_distinct_url' % (self.host, self.port)
                         )

    def test_title(self):
        self.open('/')
        self.s.wait_for_page_load()
        self.assertEqual(self.s.title, 'This is a title')

    def test_exists(self):
        pass


if __name__ == "__main__":
    unittest.main()
