import os
import unittest

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


if __name__ == "__main__":
    unittest.main()
