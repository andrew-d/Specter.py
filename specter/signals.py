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
