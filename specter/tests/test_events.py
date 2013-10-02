from .util import StaticSpecterTestCase

from specter import js_console


class TestMouseEvents(StaticSpecterTestCase):
    STATIC_FILE = 'events.html'

    def setUp(self):
        super(TestMouseEvents, self).setUp()
        self.console = []
        js_console.connect(self.onConsole)

    def tearDown(self):
        super(TestMouseEvents, self).tearDown()
        js_console.disconnect(self.onConsole)

    def onConsole(self, sender, message, line, source):
        print("Console: " + message)
        self.console.append(message)

    def test_mousedown(self):
        self.open('/')
        self.s.send_mouse_event('mousedown', 1, 1)
        self.s.app.processEvents()

        self.assertEqual(self.console[-1], 'mousedown: 1,1')

    def test_mouseup(self):
        self.open('/')
        self.s.send_mouse_event('mouseup', 2, 2)
        self.s.app.processEvents()

        self.assertEqual(self.console[-1], 'mouseup: 2,2')

    def test_click(self):
        self.open('/')
        self.s.send_mouse_event('click', 3, 3)
        self.s.app.processEvents()

        self.assertEqual(self.console[-1], 'click: 3,3')
