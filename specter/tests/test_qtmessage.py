import logging
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from PySide.QtCore import qInstallMsgHandler, qDebug, qCritical

from .util import BaseTestCase


class TestMessageProxy(BaseTestCase):
    def setup(self):
        self.stream = StringIO()
        self.handler = logging.StreamHandler(self.stream)
        self.handler.setFormatter(logging.Formatter("%(message)s"))
        self.log = logging.getLogger('specter')
        self.log.setLevel(logging.DEBUG)
        for handler in self.log.handlers:
            self.log.removeHandler(handler)
        self.log.addHandler(self.handler)

        from specter.specter import QtMessageProxy
        self.Proxy = QtMessageProxy

    def teardown(self):
        self.log.removeHandler(self.handler)
        self.handler.close()

    def test_simple(self):
        qInstallMsgHandler(self.Proxy(False))
        qCritical("Critical")
        self.assert_equal(self.stream.getvalue().strip(), "QT: Critical")

    def test_debug_no_log(self):
        qInstallMsgHandler(self.Proxy(False))
        qDebug("Debug")
        self.assert_equal(self.stream.getvalue(), "")

    def test_debug_log(self):
        qInstallMsgHandler(self.Proxy(True))
        qDebug("Debug")
        self.assert_equal(self.stream.getvalue().strip(), "QT: Debug")
