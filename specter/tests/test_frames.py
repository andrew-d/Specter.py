from .util import StaticSpecterTestCase


class TestFrames(StaticSpecterTestCase):
    STATIC_FILE = 'frames.html'

    def test_frame_names(self):
        self.open('/')
        frames = self.s.page.main_frame.child_frames
        self.assert_equal(len(frames), 2)
        self.assert_equal(frames[0].name, 'frame_a')
        self.assert_equal(frames[1].name, 'frame_b')

    def test_frame_urls(self):
        self.open('/')
        frames = self.s.page.main_frame.child_frames
        self.assert_equal(frames[0].requested_url, self.baseUrl + '/frame_a.html')
        self.assert_equal(frames[1].requested_url, self.baseUrl + '/frame_b.html')

    def test_frame_navigation(self):
        self.open('/')
        frames = self.s.page.main_frame.child_frames
        frames[0].open(frames[1].requested_url)
        self.s.wait_for_page_load()

        frames = self.s.page.main_frame.child_frames
        self.assert_equal(frames[0].requested_url, frames[1].requested_url)

    def test_frame_parent(self):
        self.open('/')
        frames = self.s.page.main_frame.child_frames

        self.assert_equal(frames[0].parent, self.s.page.main_frame)

    def test_no_parent(self):
        self.open('/')
        self.assert_true(self.s.page.main_frame.parent is None)
