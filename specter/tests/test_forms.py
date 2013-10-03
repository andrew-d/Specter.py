import os
from threading import Event

from PySide import QtWebKit

from specter.specter import ElementError, SpecterError
from .util import SpecterTestCase, parameters, parametrize
from .bottle import request, static_file


root = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    'static'
)


@parametrize
class TestForms(SpecterTestCase):
    STATIC_FILE = 'forms.html'

    def setup_app(self, app):
        # We run our application in another thread, so we need to wait for it
        # to be finished with the route before we check the form data.  This
        # event will be triggered when the submit route is done.
        self.submitted = Event()

        @app.route('/')
        def index():
            return static_file('forms.html', root=root)

        @app.route('/submit', method="POST")
        def submit():
            print("Submitted: " + str(request.forms))
            self.forms = request.forms
            self.files = request.files
            self.query = request.query
            self.submitted.set()

    def fill(self, selector, val):
        self.open('/')
        self.s.set_field_value(selector, val)
        self.s.app.processEvents()
        self.s.evaluate('document.mainform.submit();')
        self.s.wait_for(lambda: self.submitted.is_set())

    def test_checkbox(self):
        self.fill("input[name='checkbox']", 'checkbox')
        self.assert_equal(self.forms.get('checkbox'), 'checkbox')

    def test_checkbox_unchecked(self):
        self.fill("input[name='checkbox']", 'notfound')
        self.assert_equal(self.forms.get('checkbox'), None)

    def test_textarea(self):
        self.fill('textarea', 'this is some text')
        self.assert_equal(self.forms.get('textarea'), 'this is some text')

    def test_radio(self):
        self.fill("input[name='radio']", 'radio1')
        self.assert_equal(self.forms.get('radio'), 'radio1')

    def test_select(self):
        self.fill("select", "select3")
        self.assert_equal(self.forms.get('select'), 'select3')


    TEXT_FIELD_PARAMS = [
        ('color', '#FFFFFF'),
        ('date', '10/25/2013'),
        ('datetime', '10/25/2013 11:00 AM'),
        ('datetime-local', '10/25/2013 11:00 AM'),
        ('email', 'foo@bar.com'),
        ('hidden', 'hidden'),
        ('month', 'October 2013'),
        ('number', '12345'),
        ('password', 'secure'),
        ('range', '56'),
        ('search', 'query'),
        ('tel', '555-555-1234'),
        ('text', 'this is text'),
        ('time', '11:05 AM'),
        ('url', 'http://www.google.com'),
        ('week', 'Week 41, 2013'),
        ('empty', 'empty field'),
    ]

    @parameters(TEXT_FIELD_PARAMS)
    def test_text_field(self, param):
        id, val = param
        print("Testing field with ID '%s' and value '%s'" % (id, val))
        self.fill('#' + id, val)
        self.assert_equal(self.forms.get(id), val)

    def test_bad_selector(self):
        with self.assert_raises(ElementError):
            self.s.set_field_value('badsel', 'foo')

    def test_file_upload(self):
        self.fill('#file', os.path.join(root, 'upload.txt'))
        f = self.files.get('file')
        data = f.file.read()

        self.assert_equal(data.strip(), b'foobar')
        self.assert_equal(f.filename, 'upload.txt')

    def test_invalid_field(self):
        with self.assert_raises(SpecterError):
            self.fill("#button", "Can't fill me")

    def test_invalid_input_field(self):
        with self.assert_raises(SpecterError):
            self.fill("input[name='badinput']", 'badinput')
