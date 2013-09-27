import unittest

from util import SpecterTestCase

from specter.util import proxy_factory, patch


class Underlying(object):
    def __init__(self):
        self.x = 1

    def func(self, arg):
        return arg + 1

    @property
    def prop(self):
        return self.x

    @prop.setter
    def prop(self, val):
        self.x = val

    @prop.deleter
    def prop(self):
        self.x = 1


class TestProxyFactory(unittest.TestCase):
    def setUp(self):
        u = Underlying()
        pf = proxy_factory(Underlying, lambda _: u)

        class HasProxies(object):
            func = pf('func')
            prop = pf('prop')

        self.c = HasProxies()

    def test_with_function(self):
        self.assertEqual(self.c.func(1), 2)

    def test_property_getter(self):
        self.assertEqual(self.c.prop, 1)

    def test_property_setter(self):
        self.c.prop = 2
        self.assertEqual(self.c.prop, 2)

    def test_property_deleter(self):
        self.c.prop = 2
        del self.c.prop
        self.assertEqual(self.c.prop, 1)


class TestPatch(unittest.TestCase):
    def setUp(self):
        self.val = 1
        #self.nonexisting = xxx

    def test_simple_patch(self):
        self.assertEqual(self.val, 1)
        with patch(self, 'val', 2):
            self.assertEqual(self.val, 2)
        self.assertEqual(self.val, 1)

    def test_nonexistant_attr(self):
        self.assertFalse(hasattr(self, 'nonexisting'))
        with patch(self, 'nonexisting', 3):
            self.assertEqual(self.nonexisting, 3)
        self.assertFalse(hasattr(self, 'nonexisting'))

