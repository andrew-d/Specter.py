# Test ideas:
# To test Specter, we need to:
#   - Load a webpage
#   - Instantiate Specter
#   - Run a test on Specter
#   - Assert some result.

import os
import sys
import socket
import unittest
import threading
from os import path

import tornado
import tornado.httpserver
import tornado.ioloop
import tornado.wsgi
from tornado import netutil

from bottle import Bottle, static_file

sys.path.insert(0, path.abspath(path.join(path.dirname(__file__), '..', '..')))
from specter import Specter


class ServerThread(threading.Thread):
    def __init__(self, app, host='localhost', ready_event=None):
        threading.Thread.__init__(self)

        self.daemon = True
        self.app = app
        self.host = host
        self.ready_event = ready_event

    def _start_server(self):
        container = tornado.wsgi.WSGIContainer(self.app)
        http_server = tornado.httpserver.HTTPServer(container)
        family = socket.AF_INET6 if ':' in self.host else socket.AF_INET

        sock, = netutil.bind_sockets(None, address=self.host, family=family)
        self.port = sock.getsockname()[1]
        http_server.add_sockets([sock])
        return http_server

    def run(self):
        self.ioloop = tornado.ioloop.IOLoop.instance()
        self.server = self._start_server()
        if self.ready_event:
            self.ready_event.set()
        self.ioloop.start()

    def stop(self):
        self.ioloop.add_callback(self.server.stop)
        self.ioloop.add_callback(self.ioloop.stop)


class SpecterTestCase(unittest.TestCase):
    SPECTER_OPTIONS = {}

    def setupApp(self, app):
        pass

    def setUp(self):
        # Create application, and set it up.
        app = Bottle(catchall=False)
        self.setupApp(app)
        evt = threading.Event()

        # Start our application thread.
        thread = self.thread = ServerThread(app, ready_event=evt)
        thread.start()

        # Create Specter instance.
        self.s = Specter(**self.SPECTER_OPTIONS)

        # Wait for thread to be ready.
        evt.wait()

        # Get info about the server.
        self.port = self.thread.port
        self.host = self.thread.host
        self.baseUrl = "http://%s:%d" % (self.host, self.port)

    def tearDown(self):
        # Tell our thread to stop.
        self.thread.stop()

    # ----------------------------------------------------------------------
    # Utility functions
    # ----------------------------------------------------------------------

    def open(self, path, wait=True):
        """Helper that prefixes with our local address."""
        prefix = "http://%s:%d/" % (self.host, self.port)
        url = prefix + path.lstrip('/')
        ret = self.s.open(url)
        if wait:
            self.s.wait_for_page_load()
        return ret


class StaticSpecterTestCase(SpecterTestCase):
    STATIC_FILE = ''

    def setupApp(self, app):
        root = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'static'
        )

        @app.route('/<path:path>')
        def rest(path):
            print("Serving static file: %s" % (path,))
            return static_file(filename=path, root=root)

        @app.route('/')
        def index():
            print("Serving static file: %s" % (self.STATIC_FILE,))
            return static_file(filename=self.STATIC_FILE, root=root)
