import time
import logging

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
    from PySide.QtGui import QApplication, QImage, QPainter, QPrinter
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


class TimeoutError(Exception):
    """Error raised when a network operation times out."""
    pass


class SpecterWebPage(QtWebKit.QWebPage):
    def __init__(self, app, signals):
        super(SpecterWebPage, self).__init__(app)

        self.signals = signals

        # Connect to QWebPage signals.
        self.loadStarted.connect(self._loadStarted)
        self.loadStarted.connect(self._loadProgress)
        self.loadStarted.connect(self._loadFinished)

    def _loadStarted(self):
        print("loadStarted")
        #self.signals.send('loadStarted')

    def _loadProgress(self):
        print('loadProgress')
        #self.signals.send('loadProgress', progress)

    def _loadFinished(self):
        print('loadFinished')
        #self.signals.send('loadFinished', ok)


class Specter(object):
    """
    Main object
    """

    _app = None

    @property
    def app(self):
        if not Specter._app:
            Specter._app = QApplication.instance() or QApplication(['specter'])

            # TODO: debugging, plugins, etc.

        return Specter._app


    def __init__(self):
        self.signals = blinker.Namespace()
        self.page = SpecterWebPage(self.app, self.signals)

        QtWebKit.QWebSettings.setMaximumPagesInCache(0)
        QtWebKit.QWebSettings.setObjectCacheCapacities(0, 0, 0)
        QtWebKit.QWebSettings.globalSettings().setAttribute(
            QtWebKit.QWebSettings.LocalStorageEnabled, True)

        self.page.setForwardUnsupportedContent(True)

        # TODO: configure these
        self.page.settings().setAttribute(
            QtWebKit.QWebSettings.AutoLoadImages, True)
        self.page.settings().setAttribute(
            QtWebKit.QWebSettings.PluginsEnabled, True)
        self.page.settings().setAttribute(QtWebKit.QWebSettings.JavaEnabled,
            True)

        self.main_frame = self.page.mainFrame()

        # DEBUGGING: Display page
        self.webview = QtWebKit.QWebView()
        self.webview.setPage(self.page)
        self.webview.show()

    def open(self, address, method="GET"):
        body = QByteArray()
        try:
            method = getattr(QNetworkAccessManager,
                             "%sOperation" % method.capitalize())
        except AttributeError:
            raise Error("Invalid http method %s" % method)

        request = QNetworkRequest(QUrl(address))
        request.CacheLoadControl(0)
        # for header in headers:
        #     request.setRawHeader(header, headers[header])

        self.main_frame.load(request, method, body)

    def sleep(self, duration):
        start = time.time()

        while time.time() < (start + duration):
            self.app.processEvents()
            time.sleep(0.01)
