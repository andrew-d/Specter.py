import os
import time
import unittest

from specter.specter import SpecterError, TimeoutError
from .util import SpecterTestCase, StaticSpecterTestCase
from .bottle import redirect, static_file


class TestSimple(StaticSpecterTestCase):
    STATIC_FILE = 'simple.html'

    def test_simple_and_sleep(self):
        self.open('/')
        self.assert_in('This is an index page', self.s.content)

    def test_wait_for(self):
        self.open('/')
        self.s.wait_for(lambda: 'This is an index page' in self.s.content)

    def test_wait_for_text(self):
        self.open('/')
        self.s.wait_for_text('This is an index page')

    def test_url(self):
        self.open('/')
        self.assert_equal(self.s.url,
                         self.baseUrl + '/'
                         )

    def test_title(self):
        self.open('/')
        self.assert_equal(self.s.title, 'This is a title')

    def test_bad_open(self):
        with self.assert_raises(SpecterError):
            self.s.open('/foobar', method="BAD")

    def test_wait_timeout(self):
        with self.assert_raises(TimeoutError):
            self.s.wait_for(lambda: False, timeout=0.01)

    def test_sleep(self):
        start = time.time()
        self.s.sleep(0.05)
        end = time.time()

        diff = (end - start) - 0.05
        print("Difference: " + str(end - start))

        self.assert_true(diff < 0.01)

    def test_default_viewport(self):
        self.assert_equal(self.s.viewport_size, (800, 600))

    def test_timeout(self):
        self.assert_equal(self.s.page.main_frame.timeout, 90)

        # TODO: should test this is being used?
        self.s.page.main_frame.timeout = 120
        self.assert_equal(self.s.page.main_frame.timeout, 120)


if __name__ == "__main__":
    unittest.main()
