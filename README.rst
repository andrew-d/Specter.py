Specter.py
==========

.. image:: https://travis-ci.org/andrew-d/Specter.py.png?branch=master
        :target: https://travis-ci.org/andrew-d/Specter.py

Specter.py allows you to automate WebKit through Python, making tasks such as
web scraping and web application testing easier.  It uses QWebKit from the Qt
project through the `PySide <http://qt-project.org/wiki/PySide>`_ or
`PyQt <http://www.riverbankcomputing.com/software/pyqt/intro>`_ projects.


Documentation
-------------

In progress, but not currently hosted anywhere.  Here's a quick example:

.. code-block:: python

    from specter import Specter

    s = Specter()
    s.open('http://www.google.com')
    s.wait_for_page_load()
    print(s.content)
