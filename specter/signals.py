import itertools
from contextlib import contextmanager


class _Signal(object):
    """
    Object that implements the signals that are sent by Specter.  It consists
    of three concepts:
        1. Listeners.  Each listener is notified when the signal is emitted,
           and return values are discarded.
        2. Internal Listeners.  Like listeners, but internal to Specter.  These
           should not be modified.
        3. Callback.  A single callable that gets called after each listener is
           notified, and can return a value for use by the signal's emitter.
    """
    def __init__(self, name, callback_required=True):
        self.name = name
        self.listeners = []
        self.internal_listeners = []
        self.callback = None
        self.cb_required = callback_required

    def add_listener(self, listener, _internal=False):
        if _internal:
            l = self.internal_listeners
        else:
            l = self.listeners

        l.append(listener)

    def remove_listener(self, listener, _internal=False):
        if _internal:
            l = self.internal_listeners
        else:
            l = self.listeners

        try:
            while True:
                l.remove(listener)
        except ValueError:
            pass

    @contextmanager
    def with_listening(self, listener, _internal=False):
        self.add_listener(listener, _internal)
        yield
        self.remove_listener(listener, _internal)

    @property
    def has_listeners(self):
        return (len(self.listeners) + len(self.internal_listeners)) > 0

    @property
    def has_callback(self):
        return self.callback is not None

    def clear_listeners(self, _internal=False):
        if _internal:
            l = self.internal_listeners
        else:
            l = self.listeners

        del l[:]

    def set_callback(self, cb, overwrite=False):
        if self.callback is not None and not overwrite:
            raise ValueError("Callback already set, but overwrite is False")

        self.callback = cb

    def emit(self, sender, *args, **kwargs):
        if self.callback is None and self.cb_required:
            raise ValueError("No callback set for signal '%s'" % (self.name,))

        # Order matters - notify internal listeners first.
        for f in itertools.chain(self.internal_listeners, self.listeners):
            f(sender, *args, **kwargs)

        # Return nothing if we have no callback.
        if self.callback is None:
            return None

        return self.callback(sender, *args, **kwargs)

    def __repr__(self):
        return "_Signal('%s')" % (self.name,)


# Actual signals.
load_started = _Signal('load-started', False)
load_progress = _Signal('load-progress', False)
load_finished = _Signal('load-finished', False)
js_alert = _Signal('javascript-alert', False)
js_confirm = _Signal('javascript-confirm', True)
js_prompt = _Signal('javascript-prompt', True)
js_console = _Signal('javascript-console', False)
ssl_error = _Signal('ssl-error', False)
