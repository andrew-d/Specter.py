from util import StaticSpecterTestCase


class TestSelectors(StaticSpecterTestCase):
    STATIC_FILE = 'selectors.html'

    def test_exists_id(self):
        self.open('/')
        self.assertTrue(self.s.exists('#the_id'))

    def test_exists_class(self):
        self.open('/')
        self.assertTrue(self.s.exists('.the_class'))

    def test_wait_for_selector(self):
        self.open('/')
        self.assertFalse(self.s.exists('#created_id'))
        self.s.wait_for_selector('#created_id')
        self.assertTrue(self.s.exists('#created_id'))

    def test_wait_while_selector(self):
        self.open('/')
        self.assertTrue(self.s.exists('#deleteme'))
        self.s.wait_while_selector('#deleteme')
        self.assertFalse(self.s.exists('#deleteme'))
