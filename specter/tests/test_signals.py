from specter import InteractionError
from specter.signals import *
from specter.signals import _Signal

from .util import StaticSpecterTestCase, BaseTestCase


class TestSignalObject(BaseTestCase):
    def setup(self):
        self.lcalls = 0
        self.icalls = 0
        self.ccalls = 0

        self.senders = []
        self.args = []
        self.kwargs = []

        def listen(sender, *args, **kwargs):
            self.senders.append(sender)
            self.args.append(args)
            self.kwargs.append(kwargs)
            self.lcalls += 1

        def ilisten(sender, *args, **kwargs):
            self.senders.append(sender)
            self.args.append(args)
            self.kwargs.append(kwargs)
            self.icalls += 1

        def cb(sender, *args, **kwargs):
            self.senders.append(sender)
            self.args.append(args)
            self.kwargs.append(kwargs)
            self.ccalls += 1

        self.listen = listen
        self.ilisten = ilisten
        self.cb = cb

        self.s = _Signal('foo', callback_required=False)
        self.s.add_listener(listen)
        self.s.add_listener(ilisten, _internal=True)
        self.s.set_callback(cb)

    def test_repr(self):
        self.assert_equal(repr(self.s), "_Signal('foo')")

    def test_add_listeners(self):
        self.s.emit('foo')
        self.assert_equal(self.lcalls, 1)
        self.assert_equal(self.icalls, 1)
        self.assert_equal(self.ccalls, 1)

    def test_remove_listeners(self):
        self.s.remove_listener(self.listen)
        self.s.emit('foo')
        self.assert_equal(self.lcalls, 0)

    def test_remove_listeners2(self):
        self.s.remove_listener(self.ilisten, _internal=True)
        self.s.emit('foo')
        self.assert_equal(self.icalls, 0)

    def test_remove_callback(self):
        self.s.set_callback(None, overwrite=True)
        self.s.emit('foo')
        self.assert_equal(self.ccalls, 0)

    def test_clear_listeners(self):
        self.s.clear_listeners()
        self.s.emit('foo')
        self.assert_equal(self.lcalls, 0)
        self.assert_equal(self.icalls, 1)

    def test_clear_listeners2(self):
        self.s.clear_listeners(_internal=True)
        self.s.emit('foo')
        self.assert_equal(self.lcalls, 1)
        self.assert_equal(self.icalls, 0)

    def test_no_overwrite_by_default(self):
        with self.assert_raises(ValueError):
            self.s.set_callback(None)

    def test_has_listeners(self):
        self.assert_true(self.s.has_listeners)
        self.s.clear_listeners()
        self.s.clear_listeners(_internal=True)
        self.assert_false(self.s.has_listeners)

    def test_has_callback(self):
        self.assert_true(self.s.has_callback)
        self.s.set_callback(None, overwrite=True)
        self.assert_false(self.s.has_callback)

    def test_required(self):
        s = _Signal('req')
        with self.assert_raises(ValueError):
            s.emit('no cb')

    def test_temporary_listener(self):
        s = _Signal('temp', callback_required=False)
        calls = []
        def foo(s):
            calls.append(1)

        with s.with_listening(foo):
            s.emit('foo')

        self.assert_equal(sum(calls), 1)

        # Second will do nothing, since it should be removed above.
        s.emit('bar')
        self.assert_equal(sum(calls), 1)


class SignalTestCase(StaticSpecterTestCase):
    def setup(self):
        super(SignalTestCase, self).setup()
        self.calls = 0
        self.senders = []
        self.args = []
        self.kwargs = []

    def sig(self, sender, *args, **kwargs):
        self.calls += 1
        self.senders.append(sender)
        self.args.append(args)
        self.kwargs.append(kwargs)


# TODO: should verify arguments match what we expect
class TestSignals(SignalTestCase):
    STATIC_FILE = 'signals1.html'

    def test_load_started_signal(self):
        load_started.add_listener(self.sig)
        self.open('/')
        self.assert_equal(self.calls, 1)

    def test_load_progress_signal(self):
        load_progress.add_listener(self.sig)
        self.open('/')
        self.assert_true(self.calls >= 1)

    def test_load_finished_signal(self):
        load_finished.add_listener(self.sig)
        self.open('/')
        self.assert_equal(self.calls, 1)
        self.assert_true(self.args[0][0] is True)

    def test_console_signal(self):
        with js_console.with_listening(self.sig):
            self.open('/')

        self.assert_equal(self.calls, 1)

        self.assert_equal(self.args[0][0], 'Hello world')
        self.assert_equal(self.args[0][2], self.baseUrl + '/signals1.js')

        # TODO: this fails - why?
        #self.assert_equal(args[2], 4)


class TestAlert(SignalTestCase):
    STATIC_FILE = 'signals_alert.html'

    def test_alert(self):
        js_alert.add_listener(self.sig)
        self.open('/')
        self.assert_equal(self.calls, 1)
        self.assert_equal(self.args[0][0], 'This is an alert')


class TestPrompt(SignalTestCase):
    STATIC_FILE = 'signals_prompt.html'

    def prompt_sig(self, sender, message, default=None):
        self.calls += 1
        self.args.append((message, default))
        return 'prompt response'

    def alert_sig(self, sender, message):
        self.message = message

    def test_prompt(self):
        js_prompt.set_callback(self.prompt_sig)
        js_alert.add_listener(self.alert_sig)
        self.open('/')

        print(self.args)

        self.assert_equal(self.calls, 1)
        self.assert_equal(self.args[0][0], 'Prompt?')
        self.assert_equal(self.args[0][1], "default val")
        self.assert_equal(self.message, 'out: prompt response')

    def test_prompt_error(self):
        # TODO: this gets raised in a different thread or something...
        #self.assertRaises(InteractionError, self.open, '/')
        pass


class TestConfirm(SignalTestCase):
    STATIC_FILE = 'signals_confirm.html'

    def confirm_sig(self, sender, message):
        self.calls += 1
        self.args.append(message)
        return True

    def alert_sig(self, sender, message):
        self.message = message

    def test_confirm(self):
        js_confirm.set_callback(self.confirm_sig)
        js_alert.add_listener(self.alert_sig)
        self.open('/')

        self.assert_equal(self.calls, 1)
        self.assert_equal(self.args[0], 'Confirm?')
        self.assert_equal(self.message, 'out: true')

    def test_confirm_error(self):
        # TODO: this gets raised in a different thread or something...
        #self.assertRaises(InteractionError, self.open, '/')
        pass
