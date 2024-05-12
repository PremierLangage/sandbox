import os
from unittest import TestCase

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sandbox.settings")


class CloneTestCase(TestCase):
    def test_clone_ok(self):
        pass

    def test_clone_fail(self):
        pass


class PullTestCase(TestCase):
    def test_pull_ok(self):
        pass

    def test_pull_fail(self):
        pass
