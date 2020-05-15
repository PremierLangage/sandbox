import os

from .utils import DUMMY_GIT_URL, LibTestCase, TEST_EXTERNAL_LIBRARIES_ROOT
from .. import git


class CloneTestCase(LibTestCase):
    
    def test_clone_ok(self):
        path = os.path.join(TEST_EXTERNAL_LIBRARIES_ROOT, "dummy")
        self.assertFalse(os.path.isdir(path))
        self.assertEqual(0, git.clone("dummy", DUMMY_GIT_URL))
        self.assertTrue(os.path.isdir(path))
        self.assertTrue(os.path.isdir(os.path.join(path, ".git")))
    
    
    def test_clone_fail(self):
        path = os.path.join(TEST_EXTERNAL_LIBRARIES_ROOT, "dummy")
        os.mkdir(path)
        open(os.path.join(path, "file"), "w+").close()
        self.assertNotEqual(0, git.clone("dummy", DUMMY_GIT_URL))
        self.assertFalse(os.path.isdir(os.path.join(path, ".git")))


class PullTestCase(LibTestCase):
    
    def test_pull_ok(self):
        git.clone("dummy", DUMMY_GIT_URL)
        self.assertEqual(0, git.pull("dummy", DUMMY_GIT_URL))
    
    
    def test_pull_fail(self):
        path = os.path.join(TEST_EXTERNAL_LIBRARIES_ROOT, "dummy")
        os.mkdir(path)
        self.assertNotEqual(0, git.pull("dummy", DUMMY_GIT_URL))
