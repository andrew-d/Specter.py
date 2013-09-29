import os

from util import SpecterTestCase
from bottle import static_file

class TestFrames(SpecterTestCase):
    def setupApp(self, app):
        root_dir = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            "static"
        )

        @app.route('/<path:path>')
        def callback(path):
            return static_file(path, root=root_dir)

        @app.route('/')
        def index():
            return static_file('frames.html', root=root_dir)

    def test_frame_names(self):
        self.open('/')
        frames = self.s.page.main_frame.child_frames
        self.assertEqual(len(frames), 2)
        self.assertEqual(frames[0].name, 'frame_a')
        self.assertEqual(frames[1].name, 'frame_b')

    def test_frame_urls(self):
        self.open('/')
        frames = self.s.page.main_frame.child_frames
        self.assertEqual(frames[0].requested_url, self.baseUrl + '/frame_a.html')
        self.assertEqual(frames[1].requested_url, self.baseUrl + '/frame_b.html')

    def test_frame_navigation(self):
        self.open('/')
        frames = self.s.page.main_frame.child_frames
        frames[0].open(frames[1].requested_url)
        self.s.wait_for_page_load()

        frames = self.s.page.main_frame.child_frames
        self.assertEqual(frames[0].requested_url, frames[1].requested_url)

    def test_frame_parent(self):
        self.open('/')
        frames = self.s.page.main_frame.child_frames

        self.assertEqual(frames[0].parent, self.s.page.main_frame)

    def test_no_parent(self):
        self.open('/')
        self.assertTrue(self.s.page.main_frame.parent is None)
