from .util import StaticSpecterTestCase

from specter import js_console


class TestFrames(StaticSpecterTestCase):
    STATIC_FILE = 'forms.html'

    def setUp(self):
        super(TestFrames, self).setUp()
        self.console = []
        js_console.connect(self.onConsole)

    def tearDown(self):
        super(TestFrames, self).tearDown()
        js_console.disconnect(self.onConsole)

    def onConsole(self, sender, message, line, source):
        print("Console message: %s" % (message,))
        self.console.append(message)

    def test_checkbox(self):
        self.open('/')
        self.s.set_field_value("input[name='checkbox']", 'checkbox')
        self.s.app.processEvents()
        self.assertEqual(self.console[-1], 'checkbox\tchecked')

        self.s.set_field_value("input[name='checkbox']", 'notfound')
        self.s.app.processEvents()
        self.assertEqual(self.console[-1], 'checkbox\tunchecked')

    def test_textarea(self):
        self.open('/')
        self.s.set_field_value('textarea', 'some text')
        self.s.app.processEvents()

        # import webbrowser
        # webbrowser.open(self.baseUrl)
        # self.s.sleep(100)

        self.assertEqual(self.console[0], 'textarea\tsome text')
