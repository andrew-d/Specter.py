import time
import logging
from numbers import Number
from functools import wraps
from contextlib import contextmanager

import blinker

PYSIDE = False
try:
    from PySide import QtWebKit
    from PySide.QtNetwork import QNetworkRequest, QNetworkAccessManager, \
                                 QNetworkCookieJar, QNetworkDiskCache, \
                                 QNetworkProxy, QNetworkCookie
    from PySide import QtCore
    from PySide.QtCore import QSize, QByteArray, QUrl, QDateTime, \
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


class SpecterError(Exception):
    """Base class for all errors from Specter. """
    pass


class TimeoutError(SpecterError):
    """Error raised when a network operation times out."""
    pass


class InteractionError(SpecterError):
    """Error raised when there's no handlers listening for a prompt."""
    pass


class ElementError(SpecterError):
    """Error raised when Specter is unable to find an element."""
    pass


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


@contextmanager
def set_value(obj, attr, value):
    hasOld = False
    old = None
    if hasattr(obj, attr):
        old = getattr(obj, attr)
        hasOld = True

    setattr(obj, attr, value)
    yield

    if hasOld:
        setattr(obj, attr, old)


class SpecterWebPage(QtWebKit.QWebPage):
    def __init__(self, specter, signals):
        super(SpecterWebPage, self).__init__(specter.app)

        self.specter = specter
        self.signals = signals

        # Connect to QWebPage signals.
        self.loadStarted.connect(self._loadStarted)
        self.loadProgress.connect(self._loadProgress)
        self.loadFinished.connect(self._loadFinished)
        self.unsupportedContent.connect(self._unsupportedContent)

    def _loadStarted(self):
        self.signals.signal('loadStarted').send()

    def _loadProgress(self, progress):
        self.signals.signal('loadProgress').send(progress)

    def _loadFinished(self, ok):
        self.signals.signal('loadFinished').send(ok)

    def _unsupportedContent(self, reply):
        print('unsupported content!')

    def chooseFile(self, frame, suggested_file=None):
        return self.specter._file_to_upload

    def javaScriptAlert(self, frame, message):
        s = self.signals.signal('jsAlert')
        f = self.specter._frame_mapping[frame]
        s.send(f, message)

    def javaScriptConfirm(self, frame, message):
        s = self.signals.signal('jsConfirm')
        if not s.receivers:
            raise InteractionError("No handler set for JavaScript confirmation!")

        f = self.specter._frame_mapping[frame]
        ret = s.send(f, message)
        return ret

    def javaScriptPrompt(self, frame, message, defaultValue, result=None):
        s = self.signals.signal('jsPrompt')
        if not s.receivers:
            raise InteractionError("No handler set for JavaScript prompt!")

        f = self.specter._frame_mapping[frame]
        ret = s.send(f, message)

        if result is None:
            # PySide
            return True, ret
        else:
            # PyQT
            result.append(ret)
            return True

    def javaScriptConsoleMessage(self, frame, message, line, source):
        super(SpecterWebPage, self).javaScriptConsoleMessage(message, line,
            source)
        s = self.signals.signal('jsConsole')
        f = self.specter._frame_mapping[frame]
        s.send(f, message, line, source)


class WebFrame(object):
    def __init__(self, underlying, page, is_main=False):
        self._frame = underlying
        self._page = page
        self.is_main = is_main

    def open(self, address, method="GET", **kwargs):
        body = QByteArray()
        try:
            method = getattr(QNetworkAccessManager,
                             "%sOperation" % method.capitalize())
        except AttributeError:
            raise Error("Invalid http method %s" % method)

        request = QNetworkRequest(QUrl(address))
        request.CacheLoadControl(0)

        # If we have headers...
        if 'headers' in kwargs:
            for header, val in kwargs['headers'].items():
                request.setRawHeader(header, val)

        self._frame.load(request, method, body)

    def wait_for(self, predicate, timeout=None):
        # TODO: don't wait forever by default
        if timeout is None:
            timeout = float('inf')

        start = time.time()
        while time.time() < (start + timeout):
            if predicate():
                return
            self._page.app.processEvents()
            time.sleep(0.01)

        raise TimeoutError("Wait timed out")

    def sleep(self, duration):
        try:
            self.wait_for(lambda: False, duration)
        except TimeoutError:
            pass

    @property
    def parent(self):
        raw = self._frame.parentFrame()
        if raw is None:
            return None
        return self._page._frame_mapping[raw]

    @property
    def title(self):
        return self._frame.title()

    @property
    def url(self):
        return self._frame.url().toString()

    @property
    def requested_url(self):
        return self._frame.requestedUrl().toString()

    @property
    def name(self):
        return self._frame.frameName()

    @property
    def content(self):
        return self._frame.toHtml()

    # ----------------------------------------------------------------------
    # Selector functions
    def exists(self, selector):
        return not self._frame.findFirstElement(selector).isNull()


    _text_fields = frozenset([
        'color', 'date', 'datetime', 'datetime-local', 'email', 'hidden',
        'month', 'number', 'password', 'range', 'search', 'tel', 'text',
        'time', 'url', 'week',
    ])
    def set_field_value(self, selector, value, blur=True):
        el = self._frame.findFirstElement(selector)
        if el.isNull():
            raise ElementError("Unable to find element for selector: %s" % (
                selector,))

        tag = el.tagName().lower()
        if tag == 'select':
            el.setFocus()
            # TODO: evaluate JS to set value

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
                # Patch the file upload property to be our suggested value,
                # trigger the click, and then remove it.  A context manager
                # makes this easier.
                with set_value(self._page, '_file_to_upload', value):
                    # Trigger a click in Javascript.
                    self.evaluate("""
                        var element = document.querySelector("%s");
                        var evt = document.createEvent("MouseEvents");
                        evt.initMouseEvent("click", true, true, window, 1, 1, 1, 1, 1,
                            false, false, false, false, 0, element);
                        element.dispatchEvent(evt)
                    """ % selector)

            else:
                raise SpecterError('Unable to set the value of input field of '
                                   'type %s' % (ty,))

        else:
            raise SpecterError('Unable to set the value of field with type: '
                               '%s' % (tag,))

        if blur:
            self.fire_on(selector, 'blur')

    def evaluate(self, script):
        self._frame.evaluateJavaScript(str(script))
        # TODO: handle return value

    def fire_on(self, selector, event):
        self.evaluate('document.querySelector("%s").%s();' % (selector, event))

    # ----------------------------------------------------------------------
    # Helpful wait functions
    def wait_for_selector(self, selector):
        return self.wait_for(lambda: self.exists(selector))

    def wait_while_selector(self, selector):
        return self.wait_for(lambda: not self.exists(selector))

    def wait_for_text(self, text):
        return self.wait_for(lambda: text in self.content)

    def wait_for_page_load(self):
        return self.wait_for(lambda: self._page._loaded == True)


def _frame_proxy(name):
    """
    Proxy a given method or property from an underlying object to the
    current class.
    """

    f = getattr(WebFrame, name)
    if isinstance(f, property):
        def fget(self, *args, **kwargs):
            return f.fget(self._main_frame, *args, **kwargs)
        _proxy = property(fget, doc=f.__doc__)

        if f.fset is not None:
            def fset(self, *args, **kwargs):
                return f.fset(self._main_frame, *args, **kwargs)
            _proxy.fset = fset

        if f.fdel is not None:
            def fdel(self, *args, **kwargs):
                return f.fdel(self._main_frame, *args, **kwargs)
            _proxy.fdel = fdel
    else:
        @wraps(f)
        def _proxy(self, *args, **kwargs):
            return f(self._main_frame, *args, **kwargs)

    return _proxy


class SizedWebView(QtWebKit.QWebView):
    def __init__(self, size, *args, **kwargs):
        self.__size = size
        super(SizedWebView, self).__init__(*args, **kwargs)

    def sizeHint(self):
        return QSize(*self.__size)


class Specter(object):
    """
    Main object
    """

    _app = None

    @property
    def app(self):
        if not Specter._app:
            Specter._app = QApplication.instance() or QApplication(['specter'])
            qInstallMsgHandler(QTMessageProxy(False))

        return Specter._app

    def __init__(self, **options):
        self.signals = blinker.Namespace()
        self.page = SpecterWebPage(self, self.signals)

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

        # When a frame is created, we create a wrapper object for it.
        self.page.frameCreated.connect(self._frame_created)
        self._frame_mapping = {}

        # We save the main frame explicitly.
        underlying = self.page.mainFrame()
        frameObj = WebFrame(underlying, self, is_main=True)
        self._main_frame = frameObj
        self._underlying = underlying
        self._frame_mapping[underlying] = frameObj

        # Page load status
        self._loaded = False
        self.page.loadStarted.connect(self._page_load_started)
        self.page.loadFinished.connect(self._page_load_finished)

        # Size
        self._viewport_size = options.get('viewport_size', (800, 600))

        # File to upload (defaults to None - i.e. nothing).
        self._file_to_upload = None

        self.webview = None
        if options.get('display', False):
            self.webview = SizedWebView(self._viewport_size)
            self.webview.setPage(self.page)
            self.webview.show()

    def __del__(self):
        if self.webview is not None:
            self.webview.close()
        self.app.quit()

        del self.page
        del self._main_frame

    def _frame_created(self, frame):
        self._frame_mapping[frame] = WebFrame(frame, self)

    def _page_load_started(self):
        self._loaded = False
        self._frame_mapping = {self._underlying: self._main_frame}

    def _page_load_finished(self, ok):
        self._loaded = True

    @property
    def main_frame(self):
        return self._main_frame

    @property
    def viewport_size(self):
        return self._viewport_size

    @viewport_size.setter
    def viewport_size(self, newSize):
        self._viewport_size = newSize
        self.page.setViewportSize(QSize(*newSize))

    def go_back(self):
        self.page.triggerAction(QtWebKit.QWebPage.Back)

    def go_forward(self):
        self.page.triggerAction(QtWebKit.QWebPage.Forward)

    def stop(self):
        self.page.triggerAction(QtWebKit.QWebPage.Stop)

    def reload(self):
        self.page.triggerAction(QtWebKit.QWebPage.Reload)

    _mouse_mapping = {
        'mousedown': QtCore.QEvent.MouseButtonPress,
        'mouseup': QtCore.QEvent.MouseButtonRelease,
        'doubleclick': QtCore.QEvent.MouseButtonDblClick,
        'mousemove': QtCore.QEvent.MouseMove,
    }
    def send_mouse_event(self, type, x, y, button='left'):
        if type == 'click':
            # Not provided by Qt, so we just send two events.
            self.send_mouse_event('mousedown', x, y, button)
            self.send_mouse_event('mouseup', x, y, button)
            return

        x = int(x)
        y = int(y)
        eventType = self._mouse_mapping.get(type, None)
        if eventType is None:
            raise ValueError('Invalid keyboard event type: %s' % (type,))

        if button == 'left':
            buttonObj = QtCore.Qt.LeftButton
        elif button == 'right':
            buttonObj = QtCore.Qt.RightButton
        elif button == 'middle':
            buttonObj = QtCore.Qt.MiddleButton
        else:
            raise ValueError('Invalid mouse button: %s' % (button,))

        event = QMouseEvent(eventType, (x, y), buttonObj, buttonObj,
                            QtCore.Qt.NoModifier)
        self._page.app.postEvent(self._page.page, event)

    def send_keyboard_event(self, type, keys, modifiers=None):
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
        elif isinstance(keys, str) and len(keys) > 0:
            key = ord(keys[0])

        if modifiers is None:
            modifiers = QtCore.Qt.NoModifier

        event = QKeyEvent(eventType, key, modifiers)

    # Proxy some methods from the main frame to the web page.
    open                = _frame_proxy('open')
    wait_for            = _frame_proxy('wait_for')
    sleep               = _frame_proxy('sleep')
    wait_for_selector   = _frame_proxy('wait_for_selector')
    wait_while_selector = _frame_proxy('wait_while_selector')
    wait_for_text       = _frame_proxy('wait_for_text')
    wait_for_page_load  = _frame_proxy('wait_for_page_load')
    exists              = _frame_proxy('exists')
    evaluate            = _frame_proxy('evaluate')
    set_field_value     = _frame_proxy('set_field_value')
    fire_on             = _frame_proxy('fire_on')

    # Proxy properties
    url             = _frame_proxy('url')
    requested_url   = _frame_proxy('requested_url')
    title           = _frame_proxy('title')
    name            = _frame_proxy('name')
    content         = _frame_proxy('content')
