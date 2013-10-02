import time
import logging
from numbers import Number
from weakref import WeakKeyDictionary
from enum import IntEnum

import blinker

from .util import proxy_factory, patch
from .signals import *
from .exceptions import *
from .six import PY3, string_types, byte2int

PYSIDE = False
try:
    from PySide import QtWebKit
    from PySide.QtNetwork import QNetworkRequest, QNetworkAccessManager, \
                                 QNetworkCookieJar, QNetworkDiskCache, \
                                 QNetworkProxy, QNetworkCookie
    from PySide import QtCore
    from PySide.QtCore import QSize, QPoint, QByteArray, QUrl, QDateTime, \
                              QtCriticalMsg, QtDebugMsg, QtFatalMsg, \
                              QtWarningMsg, qInstallMsgHandler
    from PySide.QtGui import QApplication, QImage, QPainter, QPrinter, \
                             QMouseEvent, QKeyEvent
    PYSIDE = True
except ImportError:
    try:
        import sip
        sip.setapi('QVariant', 2)
        from PyQt4 import QtWebKit
        from PyQt4.QtNetwork import QNetworkRequest, QNetworkAccessManager, \
                                    QNetworkCookieJar, QNetworkDiskCache,  \
                                    QNetworkProxy, QNetworkCookie
        from PyQt4 import QtCore
        from PyQt4.QtCore import QSize, QByteArray, QUrl, QDateTime, \
                                 QtCriticalMsg, QtDebugMsg, QtFatalMsg, \
                                 QtWarningMsg, qInstallMsgHandler
        from PyQt4.QtGui import QApplication, QImage, QPainter, QPrinter
    except ImportError:
        raise Exception("Specter.py requires PySide or PyQt4")


logger = logging.getLogger('specter')


class QTMessageProxy(object):
    _mapping = {
        QtDebugMsg: logging.DEBUG,
        QtWarningMsg: logging.WARN,
        QtCriticalMsg: logging.CRITICAL,
        QtFatalMsg: logging.FATAL,
    }

    def __init__(self, debug=False):
        self.debug = debug

    def __call__(self, msgType, msg):
        level = self._mapping.get(msgType, logging.INFO)
        if level <= logging.WARN and not self.debug:
            return

        logger.log(level, "QT: " + msg)


class NetworkAccessManager(QNetworkAccessManager):
    def __init__(self, parent=None):
        QNetworkAccessManager.__init__(self, parent=parent)
        self._ignore_ssl_errors = False

        self.sslErrors.connect(self.handleSslErrors)

    def handleSslErrors(self, reply, errors):
        ssl_error.send(self, errors=errors)
        if self._ignore_ssl_errors:
            reply.ignoreSslErrors()

    @property
    def ignore_ssl_errors(self):
        return self._ignore_ssl_errors

    @ignore_ssl_errors.setter
    def ignore_ssl_errors(self, val):
        self._ignore_ssl_errors = val


class Modifiers(IntEnum):
    Alt = int(QtCore.Qt.KeyboardModifier.AltModifier)
    Control = int(QtCore.Qt.KeyboardModifier.ControlModifier)
    Meta = int(QtCore.Qt.KeyboardModifier.MetaModifier)
    Shift = int(QtCore.Qt.KeyboardModifier.ShiftModifier)
    No = int(QtCore.Qt.KeyboardModifier.NoModifier)


class SpecterWebFrame(object):
    def __init__(self, underlying, registry, app):
        self._frame = underlying
        self.registry = registry
        self.app = app
        self._loaded = False
        self._timeout = 90      # Matches 'network.http.connection-timeout'
                                # from Firefox

    # ----------------------------------------------------------------------
    # ----------------------------- Properties -----------------------------
    # ----------------------------------------------------------------------

    @property
    def timeout(self):
        """
        Returns the default timeout for wait operations.
        """
        return self._timeout

    @timeout.setter
    def timeout(self, val):
        """
        Set the new default timeout value.
        """
        self._timeout = float(val)

    @property
    def parent(self):
        """
        Return the parent frame of this frame, or None if this frame has no
        parent.
        """
        raw = self._frame.parentFrame()
        if raw is None:
            return None
        return self.registry.wrap(raw)

    @property
    def title(self):
        """
        Returns the title of the current frame, as set by the page's <title>
        element.
        """
        return self._frame.title()

    @property
    def url(self):
        """
        Returns the URL of the frame currently being viewed.  Note that this
        URL is not necessarily the same as the one that was originally
        requested, due to redirections or DNS.  To obtain the originally-
        requested URL, use :func:`requested_url`.
        """
        return self._frame.url().toString()

    @property
    def requested_url(self):
        """
        Returns the URL that was originally requested, before DNS resolution
        or any redirection.
        """
        return self._frame.requestedUrl().toString()

    @property
    def name(self):
        """
        Returns the name of the frame, as set by the parent.  For example::

            <html>
              <body>
                <frameset cols="50%,50%">
                  <frame src="frame_a.htm" name="frame_a">
                  <frame src="frame_b.htm" name="otherframe">
                </frameset>
              </body>
            </html>

        The names returned will be "frame_a" and "otherframe".
        """
        return self._frame.frameName()

    @property
    def content(self):
        """
        Returns a string containing the entire HTML content of this frame.
        """
        return self._frame.toHtml()

    @property
    def child_frames(self):
        """
        Returns an array of all child frames of this frame.
        """
        ret = []

        children = self._frame.childFrames()
        for child in children:
            if isinstance(child, QtWebKit.QWebFrame):
                ret.append(self.registry.wrap(child))

        return ret

    # ----------------------------------------------------------------------
    # ------------------------------ Methods -------------------------------
    # ----------------------------------------------------------------------

    def open(self, address, method="GET", **kwargs):
        """
        Open a URL in the current frame.

        :param address: the url to open
        :param method: the HTTP method to use.  Defaults to 'GET'.
        """
        body = QByteArray()
        try:
            method = getattr(QNetworkAccessManager,
                             "%sOperation" % method.capitalize())
        except AttributeError:
            raise SpecterError("Invalid http method %s" % method)

        request = QNetworkRequest(QUrl(address))
        request.CacheLoadControl(0)

        # If we have headers...
        if 'headers' in kwargs:
            for header, val in kwargs['headers'].items():
                request.setRawHeader(header, val)

        self._frame.load(request, method, body)

    def wait_for(self, predicate, timeout=None):
        """
        Wait for a given predicate to be true, waiting up to :attr:`timeout`
        seconds.  If the operaton times out, then a :class:`TimeoutError` will
        be raised.

        :param predicate: a callable that is called to determine if the wait
                          operation has succeeded.
        :param timeout: a timeout value, in seconds.  Fractional seconds (as
                        a float) are accepted.
        """
        if timeout is None:
            timeout = self.timeout

        start = time.time()
        while time.time() < (start + timeout):
            if predicate():
                return
            self.app.processEvents()
            time.sleep(0.01)

        raise TimeoutError("Wait timed out")

    def sleep(self, duration):
        """
        Pause execution for the given duration.  Note that the underlying
        WebKit instance will still continue to process events.

        :param duration: the time to sleep for, in seconds.
        """
        try:
            self.wait_for(lambda: False, duration)
        except TimeoutError:
            pass

    def exists(self, selector):
        """
        Returns whether or not an element matching the given CSS selector
        exists in the current frame.

        :param selector: a CSS selector.
        """
        return not self._frame.findFirstElement(selector).isNull()

    _text_fields = frozenset([
        '', 'color', 'date', 'datetime', 'datetime-local', 'email', 'hidden',
        'month', 'number', 'password', 'range', 'search', 'tel', 'text',
        'time', 'url', 'week',
    ])

    def set_field_value(self, selector, value, blur=True):
        """
        Set the value of a field matching the given CSS selector the given
        value.  If :attr:`blur` argument is True, then the field will lose
        focus after the value has been entered.

        :param selector: a CSS selector matching a valid element.
        :param value: the value to set on the given element.
        :param blur: whether or not to trigger a 'lose focus' event on the
                     element. Defaults to True.
        """
        el = self._frame.findFirstElement(selector)
        if el.isNull():
            raise ElementError("Unable to find element for selector: %s" % (
                selector,))

        tag = el.tagName().lower()
        if tag == 'select':
            el.setFocus()
            # Trigger this change via JavaScript.
            code = 'document.querySelector("%s").value = "%s";' % (
                selector.replace('"', '\"'),
                value.replace('"', '\"')
            )
            self.evaluate(code)

        elif tag == 'textarea':
            el.setFocus()
            el.setPlainText(value)

        elif tag == 'input':
            ty = el.attribute('type').lower()
            if ty in self._text_fields:
                el.setFocus()
                el.setAttribute('value', value)

            elif ty == 'checkbox':
                allElems = self._frame.findAllElements(selector)
                for chk in allElems:
                    chk.setFocus()
                    if chk.attribute('value') == value:
                        chk.setAttribute('checked', 'checked')
                    else:
                        chk.removeAttribute('checked')

            elif ty == 'radio':
                allElems = self._frame.findAllElements(selector)
                for radio in allElems:
                    if radio.attribute('value') == value:
                        radio.setFocus()
                        radio.setAttribute('checked', 'checked')

            elif ty == 'file':
                # We patch our parent page's file-upload value to be the given
                # value, so that the following JavaScript will result in the
                # given file being selected.
                page = self.page()
                with patch(page, '_file_to_upload', value):
                    # Trigger a click in Javascript.
                    self.evaluate("""
                        var element = document.querySelector("%s");
                        var evt = document.createEvent("MouseEvents");
                        evt.initMouseEvent("click", true, true, window, 1, 1,
                              1, 1, 1, false, false, false, false, 0, element);
                        element.dispatchEvent(evt)
                    """ % selector)

                    # Ensure events are processed.
                    # TODO: want to do this?
                    self.app.processEvents()

            else:
                raise SpecterError('Unable to set the value of input field of '
                                   'type %s' % (ty,))

        else:
            raise SpecterError('Unable to set the value of field with type: '
                               '%s' % (tag,))

        if blur:
            self.fire_on(selector, 'blur')

    def evaluate(self, script):
        """
        Evaluate the given JavaScript in the context of the current frame.

        :param script: The JavaScript to execute.
        """
        self._frame.evaluateJavaScript(str(script))
        # TODO: handle return value

    def fire_on(self, selector, event):
        """
        Trigger an event on the given selector.

        :param selector: a CSS selector.
        :param event: the event to trigger.
        """
        self.evaluate('document.querySelector("%s").%s();' % (selector, event))

    def wait_for_selector(self, selector):
        """
        Wait for an element matching the given CSS selector to exist in the
        current frame.

        :param selector: a CSS selector.
        """
        return self.wait_for(lambda: self.exists(selector))

    def wait_while_selector(self, selector):
        """
        Wait until an element matching the given CSS selector does not exist in
        the current frame.

        :param selector: a CSS selector.
        """
        return self.wait_for(lambda: not self.exists(selector))

    def wait_for_text(self, text):
        """
        Waits until the given text is present in the current frame.

        :param text: the text to search for.
        """
        return self.wait_for(lambda: text in self.content)

    def wait_for_page_load(self):
        """
        Wait until the current frame has finished loading.
        """
        page = self._frame.page()
        return self.wait_for(lambda: page.loaded is True)


class FrameRegistry(object):
    """
    This class implements a method to keep track of wrapped frames.  In short,
    Qt will give us frames that are QWebFrames, and we want to only deal with
    WebFrames that we control.  This registry will either wrap a given frame,
    or return the previously-wrapped one from the registry.
    """
    def __init__(self, klass, *args, **kwargs):
        self._registry = WeakKeyDictionary()
        self.klass = klass
        self.args = args
        self.kwargs = kwargs

    def wrap(self, frame):
        if frame is None:
            return None

        existing = self._registry.get(frame)
        if existing is not None:
            return existing

        # Create web frame, passing the underlying value, and ourselves.
        new = self.klass(frame, self, *self.args, **self.kwargs)
        self._registry[frame] = new
        return new

    def clear(self):
        del self._registry[:]


# FIXME: This won't handle custom classes
frame_proxy = proxy_factory(SpecterWebFrame, lambda self: self._main_frame)


class SpecterWebPage(QtWebKit.QWebPage):
    def __init__(self, app, registry):
        super(SpecterWebPage, self).__init__(app)

        self.app = app
        self.registry = registry
        self.loaded = False

        # This gets patched by sub-frames.  Sadly, no nicer way.
        self._file_to_upload = None

        # Connect to QWebPage signals.
        self.loadStarted.connect(self.onLoadStarted)
        self.loadProgress.connect(self.onLoadProgress)
        self.loadFinished.connect(self.onLoadFinished)
        self.unsupportedContent.connect(self.onUnsupportedContent)

    @property
    def main_frame(self):
        return self.registry.wrap(self.mainFrame())

    # ----------------------------------------------------------------------
    # ------------------------------ Signals -------------------------------
    # ----------------------------------------------------------------------

    def onLoadStarted(self):
        self.loaded = False
        load_started.send(self)

    def onLoadProgress(self, progress):
        load_progress.send(self, progress=progress)

    def onLoadFinished(self, ok):
        self.loaded = True
        load_finished.send(self, ok=ok)

    def onUnsupportedContent(self, reply):
        # TODO: fix
        print('unsupported content!')

    # ----------------------------------------------------------------------
    # -------------------------- Abstract Methods --------------------------
    # ----------------------------------------------------------------------

    def chooseFile(self, frame, suggested_file=None):
        return self._file_to_upload

    def javaScriptAlert(self, frame, message):
        js_alert.send(self.registry.wrap(frame), message=message)

    def javaScriptConfirm(self, frame, message):
        if not js_confirm.receivers:
            raise InteractionError("No handler set for JavaScript confirm!")

        ret = js_confirm.send(self.registry.wrap(frame), message=message)

        # Take the first boolean value.
        response = False
        for responder, val in ret:
            if isinstance(val, bool):
                response = val
                break

        return response

    def javaScriptPrompt(self, frame, message, defaultValue, result=None):
        if not js_prompt.receivers:
            raise InteractionError("No handler set for JavaScript prompt!")

        ret = js_prompt.send(self.registry.wrap(frame),
                             message=message, default=defaultValue)

        # We take the first non-empty return value, since blinker returns all
        # return values as a list.
        response = ''
        for responder, val in ret:
            if len(val) > 0 and isinstance(val, str):
                response = val
                break

        # NOTE: The final 'result' parameter differs between PySide and PyQt.
        if result is None:      # pragma: no cover
            return True, response
        else:                   # pragma: no cover
            result.append(response)
            return True

    def javaScriptConsoleMessage(self, message, line, source):
        super(SpecterWebPage, self).javaScriptConsoleMessage(message, line,
                                                             source)
        js_console.send(self, message=message, line=line, source=source)

    # ----------------------------------------------------------------------
    # ------------------------- Page-Level Methods -------------------------
    # ----------------------------------------------------------------------

    def go_back(self):
        """
        Go back to the previous page in the browser history.
        """
        self.triggerAction(QtWebKit.QWebPage.Back)

    def go_forward(self):
        """
        Go forward to the next page in the browser history.
        """
        self.triggerAction(QtWebKit.QWebPage.Forward)

    def stop(self):
        """
        Stop the page from loading any further.
        """
        self.triggerAction(QtWebKit.QWebPage.Stop)

    def reload(self):
        """
        Reload the current page.
        """
        self.triggerAction(QtWebKit.QWebPage.Reload)

    _mouse_mapping = {
        'mousedown': QtCore.QEvent.MouseButtonPress,
        'mouseup': QtCore.QEvent.MouseButtonRelease,
        'doubleclick': QtCore.QEvent.MouseButtonDblClick,
        'mousemove': QtCore.QEvent.MouseMove,
    }

    def send_mouse_event(self, type, x, y, button='left'):
        """
        Send a mouseclick to the current page, with parameters specified by
        the arguments given.

        :param type: the type of event to send.  Valid types are 'mousedown',
                     'mouseup', 'mousemove', 'doubleclick', and 'click'.
        :param x: the X-coordinate on which to click.
        :param y: the Y-coordinate on which to click.
        :param button: the button to click with.  Defaults to the left mouse
                       button.
        """

        # TODO: x, y relative to what?
        if type == 'click':
            # Not provided by Qt, so we just send two events.
            self.send_mouse_event('mousedown', x, y, button)
            self.send_mouse_event('mouseup', x, y, button)
            return

        x = int(x)
        y = int(y)
        eventType = self._mouse_mapping.get(type, None)
        if eventType is None:
            raise ValueError('Invalid mouse event type: %s' % (type,))

        if button == 'left':
            buttonObj = QtCore.Qt.LeftButton
        elif button == 'right':
            buttonObj = QtCore.Qt.RightButton
        elif button == 'middle':
            buttonObj = QtCore.Qt.MiddleButton
        else:
            raise ValueError('Invalid mouse button: %s' % (button,))

        event = QMouseEvent(eventType, QPoint(x, y), buttonObj, buttonObj,
                            QtCore.Qt.NoModifier)
        self.app.postEvent(self, event)
        # TODO: process events?

    def send_keyboard_event(self, type, keys, modifiers=None):
        """
        Send a keyboard event to the current page, with parameters specified by
        the arguments given.

        :param type: the type of event to send.  Valid types are 'keydown',
                     'keyup', and 'keypress'.
        :param keys: the key to send.  If this is a number, it's assumed to be
                     the keycode to send - otherwise, the keycode of the first
                     character in the given iterable is used.
        :param modifiers: modifier keys for the given event.
        """
        if type == 'keypress':
            # TODO: implement
            return

        if type == 'keydown':
            eventType = QKeyEvent.KeyPress
        elif type == 'keyup':
            eventType = QKeyEvent.KeyRelease
        else:
            raise ValueError('Invalid keyboard event type: %s' % (type,))

        key = 0
        if isinstance(keys, Number):
            key = int(keys)
        elif isinstance(keys, string_types) and len(keys) > 0:
            # Handle all four cases here - Python 2/3, unicode/bytes
            if PY3:
                if isinstance(keys, str):
                    key = ord(keys[0])
                elif isinstance(keys, bytes):
                    key = keys[0]
            else:
                if isinstance(keys, basestring):
                    key = ord(keys[0])

        if modifiers is None:
            modifiers = Modifiers.No

        event = QKeyEvent(eventType, key, modifiers)
        self.app.postEvent(self, event)
        # TODO: process events?

    # ----------------------------------------------------------------------
    # --------------------- Frame-Level Proxy Methods ----------------------
    # ----------------------------------------------------------------------

    # Proxy some methods from the main frame to the web page.
    open                = frame_proxy('open')
    wait_for            = frame_proxy('wait_for')
    sleep               = frame_proxy('sleep')
    wait_for_selector   = frame_proxy('wait_for_selector')
    wait_while_selector = frame_proxy('wait_while_selector')
    wait_for_text       = frame_proxy('wait_for_text')
    wait_for_page_load  = frame_proxy('wait_for_page_load')
    exists              = frame_proxy('exists')
    evaluate            = frame_proxy('evaluate')
    set_field_value     = frame_proxy('set_field_value')
    fire_on             = frame_proxy('fire_on')

    # Proxy properties
    url             = frame_proxy('url')
    requested_url   = frame_proxy('requested_url')
    title           = frame_proxy('title')
    name            = frame_proxy('name')
    content         = frame_proxy('content')


class SizedWebView(QtWebKit.QWebView):
    def __init__(self, size, *args, **kwargs):
        self.__size = size
        super(SizedWebView, self).__init__(*args, **kwargs)

    def sizeHint(self):
        return QSize(*self.__size)


# FIXME: these won't handle custom classes!
page_proxy = proxy_factory(SpecterWebPage, lambda self: self.page)
page_frame_proxy = proxy_factory(SpecterWebFrame,
                                 lambda self: self.page.main_frame)


class Specter(object):
    """
    The main object that contains a single web page and all the associated
    information - for example, the display.  This proxies some methods from the
    page to the current object, for convenience.
    """

    _app = None

    @property
    def app(self):
        if not Specter._app:
            Specter._app = QApplication.instance() or QApplication(['specter'])
            qInstallMsgHandler(QTMessageProxy(False))

        return Specter._app

    def __init__(self, **options):
        self.webview = None
        self.manager = NetworkAccessManager()
        self.FrameClass = options.get('frame_class', SpecterWebFrame)
        self.PageClass = options.get('page_class', SpecterWebPage)
        self.frame_registry = FrameRegistry(self.FrameClass, self.app)
        self.page = self.PageClass(self.app, self.frame_registry)
        self.page.setNetworkAccessManager(self.manager)

        QtWebKit.QWebSettings.setMaximumPagesInCache(0)
        QtWebKit.QWebSettings.setObjectCacheCapacities(0, 0, 0)
        QtWebKit.QWebSettings.globalSettings().setAttribute(
            QtWebKit.QWebSettings.LocalStorageEnabled,
            options.get('local_storage', True)
        )

        self.page.setForwardUnsupportedContent(True)

        self.page.settings().setAttribute(
            QtWebKit.QWebSettings.AutoLoadImages,
            options.get('load_images', True)
        )
        self.page.settings().setAttribute(
            QtWebKit.QWebSettings.PluginsEnabled,
            options.get('enable_plugins', True)
        )
        self.page.settings().setAttribute(
            QtWebKit.QWebSettings.JavaEnabled,
            options.get('enable_java', True)
        )

        # Size
        self.viewport_size = options.get('viewport_size', (800, 600))

        # Create webview if we are to display things.
        if options.get('display', False):
            self.webview = SizedWebView(self._viewport_size)
            self.webview.setPage(self.page)
            self.webview.show()

    def __del__(self):                      # pragma: no cover
        if self.webview is not None:
            self.webview.close()
        self.app.quit()

        del self.page

    @property
    def viewport_size(self):
        """
        Returns the given viewport size.
        """
        return self._viewport_size

    @viewport_size.setter
    def viewport_size(self, newSize):
        self._viewport_size = newSize
        self.page.setViewportSize(QSize(*newSize))

    # Page-level functions.
    go_back             = page_proxy('go_back')
    go_forward          = page_proxy('go_forward')
    stop                = page_proxy('stop')
    reload              = page_proxy('reload')
    send_mouse_event    = page_proxy('send_mouse_event')
    send_keyboard_event = page_proxy('send_keyboard_event')

    # Proxy some methods from the main frame.
    open                = page_frame_proxy('open')
    wait_for            = page_frame_proxy('wait_for')
    sleep               = page_frame_proxy('sleep')
    wait_for_selector   = page_frame_proxy('wait_for_selector')
    wait_while_selector = page_frame_proxy('wait_while_selector')
    wait_for_text       = page_frame_proxy('wait_for_text')
    wait_for_page_load  = page_frame_proxy('wait_for_page_load')
    exists              = page_frame_proxy('exists')
    evaluate            = page_frame_proxy('evaluate')
    set_field_value     = page_frame_proxy('set_field_value')
    fire_on             = page_frame_proxy('fire_on')

    # Proxy properties
    url             = page_frame_proxy('url')
    requested_url   = page_frame_proxy('requested_url')
    title           = page_frame_proxy('title')
    name            = page_frame_proxy('name')
    content         = page_frame_proxy('content')
