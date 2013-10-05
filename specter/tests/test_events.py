from .util import StaticSpecterTestCase

from specter import js_console


class TestMouseEvents(StaticSpecterTestCase):
    STATIC_FILE = 'events.html'

    def setup(self):
        super(TestMouseEvents, self).setup()
        self.console = []
        js_console.add_listener(self.onConsole)

    def teardown(self):
        super(TestMouseEvents, self).teardown()
        js_console.remove_listener(self.onConsole)

    def onConsole(self, sender, message, line, source):
        print("Console: " + message)
        self.console.append(message)

    def test_mousedown(self):
        self.open('/')
        self.s.send_mouse_event('mousedown', 1, 1)
        self.s.app.processEvents()

        self.assert_equal(self.console[-1], 'mousedown: 1,1,1')

    def test_mouseup(self):
        self.open('/')
        self.s.send_mouse_event('mouseup', 2, 2)
        self.s.app.processEvents()

        self.assert_equal(self.console[-1], 'mouseup: 2,2,1')

    def test_click(self):
        self.open('/')
        self.s.send_mouse_event('click', 3, 3)
        self.s.app.processEvents()

        self.assert_equal(self.console[-1], 'click: 3,3,1')

    def test_middle_click(self):
        self.open('/')
        self.s.send_mouse_event('mousedown', 4, 4, button='middle')
        self.s.app.processEvents()

        self.assert_equal(self.console[-1], 'mousedown: 4,4,2')

    def test_right_click(self):
        self.open('/')
        self.s.send_mouse_event('mousedown', 5, 5, button='right')
        self.s.app.processEvents()

        self.assert_equal(self.console[-1], 'mousedown: 5,5,3')

    def test_invalid_click(self):
        with self.assert_raises(ValueError):
            self.s.send_mouse_event('mousedown', 4, 4, button='invalid')

    def test_invalid_event(self):
        with self.assert_raises(ValueError):
            self.s.send_mouse_event('invalid', 1, 1)


class TestKeyboardEvents(StaticSpecterTestCase):
    STATIC_FILE = 'events.html'

    def setup(self):
        super(TestKeyboardEvents, self).setup()
        self.console = []
        js_console.add_listener(self.onConsole)

    def teardown(self):
        super(TestKeyboardEvents, self).teardown()
        js_console.remove_listener(self.onConsole)

    def onConsole(self, sender, message, line, source):
        print("Console: " + message)
        self.console.append(message)

    def test_keydown(self):
        self.open('/')
        self.s.send_keyboard_event('keydown', 'a')
        self.s.app.processEvents()

        self.assert_equal(self.console[-1], 'keydown: 65,0,0,0,0')

    def test_keydown_with_keycode(self):
        self.open('/')
        self.s.send_keyboard_event('keydown', 66)
        self.s.app.processEvents()

        self.assert_equal(self.console[-1], 'keydown: 66,0,0,0,0')

    def test_keyup(self):
        self.open('/')
        self.s.send_keyboard_event('keydown', 'a')
        self.s.app.processEvents()
        self.s.send_keyboard_event('keyup', 'a')
        self.s.app.processEvents()

        self.assert_equal(self.console[-1], 'keyup: 65,0,0,0,0')

    def test_keypress(self):
        self.open('/')
        self.s.send_keyboard_event('keypress', 'a')
        self.s.app.processEvents()

        self.assert_equal(self.console[-2], 'keydown: 65,0,0,0,0')
        self.assert_equal(self.console[-1], 'keyup: 65,0,0,0,0')

    def test_invalid_keyevent(self):
        with self.assert_raises(ValueError):
            self.s.send_keyboard_event('foobar', '')

    # TODO: test modifier keys.
