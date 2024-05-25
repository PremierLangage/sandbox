import os
import shutil
import uuid

from unittest import TestCase
from sandbox import git


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sandbox.settings")

TEST_EXTERNAL_LIBRARIES_ROOT = os.path.join("/tmp/sandbox/", str(uuid.uuid4()))
DUMMY_GIT_URL = "https://github.com/github/practice"


class CloneTestCase(TestCase):
    def setUp(self):
        super().setUp()
        os.makedirs(TEST_EXTERNAL_LIBRARIES_ROOT)

    def tearDown(self):
        super().tearDown()
        shutil.rmtree(TEST_EXTERNAL_LIBRARIES_ROOT)

    def test_clone_ok(self):
        path = os.path.join(TEST_EXTERNAL_LIBRARIES_ROOT, "dummy")
        self.assertFalse(os.path.isdir(path))
        self.assertEqual(
            0, git.clone("dummy", DUMMY_GIT_URL, TEST_EXTERNAL_LIBRARIES_ROOT)
        )
        self.assertTrue(os.path.isdir(path))
        self.assertTrue(os.path.isdir(os.path.join(path, ".git")))

    def test_clone_fail(self):
        path = os.path.join(TEST_EXTERNAL_LIBRARIES_ROOT, "dummy")
        os.mkdir(path)
        open(os.path.join(path, "file"), "w+").close()
        self.assertNotEqual(0, git.clone("dummy", DUMMY_GIT_URL))
        self.assertFalse(os.path.isdir(os.path.join(path, ".git")))


class PullTestCase(TestCase):
    def test_pull_ok(self):
        pass

    def test_pull_fail(self):
        pass
