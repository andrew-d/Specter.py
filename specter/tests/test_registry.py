from .util import BaseTestCase

from specter.specter import FrameRegistry


class _DummyClass(object):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class RefMe(object):
    pass


class TestFrameRegistry(BaseTestCase):
    def create(self, *args, **kwargs):
        self.r = FrameRegistry(_DummyClass, *args, **kwargs)
        self.o = RefMe()

    def test_wrap(self):
        self.create()
        x = self.r.wrap(self.o)
        self.assert_is_instance(x, _DummyClass)
        self.assert_true(x.args[0] is self.o)
        self.assert_true(x.args[1] is self.r)
        self.assert_equal(len(x.kwargs), 0)

    def test_wrap_args(self):
        self.create('a', arg='val')
        x = self.r.wrap(self.o)

        self.assert_true(x.args[0] is self.o)
        self.assert_true(x.args[1] is self.r)
        self.assert_equal(x.args[2], 'a')
        self.assert_equal(x.kwargs, {'arg': 'val'})

    def test_wrap_none(self):
        self.create()
        self.assert_equal(self.r.wrap(None), None)

    def test_wrap_twice(self):
        self.create()

        one = self.r.wrap(self.o)
        two = self.r.wrap(self.o)

        self.assert_true(one is two)

    def test_clear_registry(self):
        self.create()

        one = self.r.wrap(self.o)
        self.r.clear()
        two = self.r.wrap(self.o)

        self.assert_true(one is not two)
