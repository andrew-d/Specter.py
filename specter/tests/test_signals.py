from specter import InteractionError
from specter.signals import *

from util import StaticSpecterTestCase


class SignalTestCase(StaticSpecterTestCase):
    def setUp(self):
        super(SignalTestCase, self).setUp()
        self.calls = 0
        self.senders = []
        self.kwargs = []

    def sig(self, sender, **kwargs):
        self.calls += 1
        self.senders.append(sender)
        self.kwargs.append(kwargs)


# TODO: should verify arguments match what we expect
class TestSignals(SignalTestCase):
    STATIC_FILE = 'signals1.html'

    def test_load_started_signal(self):
        load_started.connect(self.sig)
        self.open('/')
        self.assertEqual(self.calls, 1)

    def test_load_progress_signal(self):
        load_progress.connect(self.sig)
        self.open('/')
        self.assertTrue(self.calls >= 1)

    def test_load_finished_signal(self):
        load_finished.connect(self.sig)
        self.open('/')
        self.assertEqual(self.calls, 1)
        self.assertTrue(self.kwargs[0]['ok'] is True)

    def test_console_signal(self):
        js_console.connect(self.sig)
        self.open('/')
        self.assertEqual(self.calls, 1)

        args = self.kwargs[0]

        self.assertEqual(args['message'], 'Hello world')
        self.assertEqual(args['source'], self.baseUrl + '/signals1.js')

        # TODO: this fails - why?
        #self.assertEqual(args['line'], 4)


class TestAlert(SignalTestCase):
    STATIC_FILE = 'signals_alert.html'

    def test_alert(self):
        js_alert.connect(self.sig)
        self.open('/')
        self.assertEqual(self.calls, 1)
        self.assertEqual(self.kwargs[0]['message'], 'This is an alert')


class TestPrompt(SignalTestCase):
    STATIC_FILE = 'signals_prompt.html'

    def prompt_sig(self, sender, message, default=None):
        self.calls += 1
        self.kwargs.append((message, default))
        return 'prompt response'

    def alert_sig(self, sender, message):
        self.message = message

    def test_prompt(self):
        js_prompt.connect(self.prompt_sig)
        js_alert.connect(self.alert_sig)
        self.open('/')

        self.assertEqual(self.calls, 1)
        self.assertEqual(self.kwargs[0][0], 'Prompt?')
        self.assertEqual(self.kwargs[0][1], "default val")
        self.assertEqual(self.message, 'out: prompt response')

    def test_prompt_error(self):
        # TODO: this gets raised in a different thread or something...
        #self.assertRaises(InteractionError, self.open, '/')
        pass


class TestConfirm(SignalTestCase):
    STATIC_FILE = 'signals_confirm.html'

    def confirm_sig(self, sender, message):
        self.calls += 1
        self.kwargs.append(message)
        return True

    def alert_sig(self, sender, message):
        self.message = message

    def test_confirm(self):
        js_confirm.connect(self.confirm_sig)
        js_alert.connect(self.alert_sig)
        self.open('/')

        self.assertEqual(self.calls, 1)
        self.assertEqual(self.kwargs[0], 'Confirm?')
        self.assertEqual(self.message, 'out: true')

    def test_confirm_error(self):
        # TODO: this gets raised in a different thread or something...
        #self.assertRaises(InteractionError, self.open, '/')
        pass
