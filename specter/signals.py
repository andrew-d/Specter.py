import itertools

import blinker


# Namespace for signals.
_signals = blinker.Namespace()


# Actual signals.
load_started = _signals.signal('load-started')
load_progress = _signals.signal('load-progress')
load_finished = _signals.signal('load-finished')
js_alert = _signals.signal('javascript-alert')
js_confirm = _signals.signal('javascript-confirm')
js_prompt = _signals.signal('javascript-prompt')
js_console = _signals.signal('javascript-console')
ssl_error = _signals.signal('ssl-error')


class _Signal(object):
    """
    Object that implements the signals that are sent by Specter.  It consists
    of three concepts::
        1. Listeners.  Each listener is notified when the signal is called, and
           return values are discarded.
        2. Internal Listeners.  Like listeners, but internal to Specter.  These
           should not be modified.
        3. Callback.  A single callable that gets called after each listener is
           notified, and can return a value for use by the signal's caller.
    """
    def __init__(self, name):
        self.name = name
        self.listeners = []
        self.internal_listeners = []
        self.callback = None

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

    def call(self, sender, *args, _required=True, **kwargs):
        if not self.callback and _required:
            raise ValueError("No callback set for signal '%s'" % (self.name,))

        # Order matters - notify internal listeners first.
        for f in itertools.chain(self.internal_listeners, self.listeners):
            f(sender, *args, **kwargs)

        # Return nothing if we have no callback.
        if not self.callback:
            return None

        return self.callback(sender, *args, **kwargs)
