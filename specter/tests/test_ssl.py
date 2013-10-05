import os
import socket
import threading

import tornado
from tornado import netutil

from .util import SpecterTestCase, BaseTestCase
from specter.specter import NetworkAccessManager, Specter
from specter.signals import ssl_error


class DummyHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("dummy")


class SSLThread(threading.Thread):
    def __init__(self, certfile, keyfile, host='localhost'):
        threading.Thread.__init__(self)
        self.certfile = certfile
        self.keyfile = keyfile
        self.host = host
        self.ready_event = threading.Event()

    def _make_server(self):
        app = tornado.web.Application([
            (r"/", DummyHandler),
        ])
        http_server = tornado.httpserver.HTTPServer(
            app,
            ssl_options={
                'certfile': self.certfile,
                'keyfile': self.keyfile,
            },
        )
        family = socket.AF_INET6 if ':' in self.host else socket.AF_INET

        sock, = netutil.bind_sockets(None, address=self.host, family=family)
        self.port = sock.getsockname()[1]
        http_server.add_sockets([sock])
        return http_server

    def run(self):
        self.ioloop = tornado.ioloop.IOLoop.instance()
        self.server = self._make_server()
        self.ready_event.set()
        self.ioloop.start()

    def stop(self):
        self.ioloop.add_callback(self.server.stop)
        self.ioloop.add_callback(self.ioloop.stop)


class TestSSL(SpecterTestCase):
    def setup(self):
        super(TestSSL, self).setup()
        self.mgr = NetworkAccessManager()

    def test_doesnt_ignore_ssl_by_default(self):
        self.assert_false(self.mgr.ignore_ssl_errors)

    def test_can_change(self):
        self.assert_false(self.mgr.ignore_ssl_errors)
        self.mgr.ignore_ssl_errors = True
        self.assert_true(self.mgr.ignore_ssl_errors)


class TestSSLInvalidCert(BaseTestCase):
    def setup(self):
        root = os.path.abspath(os.path.dirname(__file__))
        self.thread = SSLThread(
            os.path.join(root, 'server_invalid.crt'),
            os.path.join(root, 'server_invalid.key')
        )
        self.thread.start()

        self.s = Specter()

        self.thread.ready_event.wait()
        self.port = self.thread.port
        self.host = self.thread.host
        self.url = "https://%s:%d/" % (self.host, self.port)

        self.msgs = []
        ssl_error.add_listener(self.on_ssl_error)

    def teardown(self):
        self.thread.stop()

    def on_ssl_error(self, sender, errors):
        self.msgs.append(errors)

    def test_sends_ssl_error_signal(self):
        self.s.open(self.url)
        self.s.wait_for_page_load()
        self.assert_equal(len(self.msgs), 1)

    def test_will_not_load_by_default(self):
        self.s.open(self.url)
        self.s.wait_for_page_load()
        self.assert_false('dummy' in self.s.content)

        self.assert_false(self.s.manager.ignore_ssl_errors)

    def test_will_load_when_ignoring(self):
        self.s.manager.ignore_ssl_errors = True

        self.s.open(self.url)
        self.s.wait_for_page_load()
        self.assert_true('dummy' in self.s.content)
