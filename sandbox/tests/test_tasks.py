import os
import time
import uuid
from django.test import override_settings
from sandbox import git, tasks
from sandbox.tests.utils import (
    DUMMY_GIT_URL,
    TEST_ENVIRONMENT_ROOT,
    TEST_EXTERNAL_LIBRARIES_ROOT,
    SandboxTestCase,
)


class RemoveOutdatedEnvTestCase(SandboxTestCase):
    @override_settings(ENVIRONMENT_EXPIRATION=1)
    def test_remove_outdated_env(self):
        file1 = os.path.join(TEST_ENVIRONMENT_ROOT, str(uuid.uuid4()))
        file2 = os.path.join(TEST_ENVIRONMENT_ROOT, str(uuid.uuid4()))

        open(file1, "w+").close()
        time.sleep(1)
        open(file2, "w+").close()

        self.assertTrue(os.path.exists(file1))
        self.assertTrue(os.path.exists(file2))

        tasks.remove_expired_env()

        self.assertFalse(os.path.exists(file1))
        self.assertTrue(os.path.exists(file2))


class RefreshExternalLibsTestCase(SandboxTestCase):
    @override_settings(
        EXTERNAL_LIBRARIES=[
            (DUMMY_GIT_URL, "dummy1"),
            (DUMMY_GIT_URL, "dummy2"),
        ]
    )
    def test_refresh_external_libs(self):
        dummy1 = os.path.join(TEST_EXTERNAL_LIBRARIES_ROOT, "dummy1")
        dummy2 = os.path.join(TEST_EXTERNAL_LIBRARIES_ROOT, "dummy2")
        git.clone("dummy1", DUMMY_GIT_URL)

        tasks.refresh_external_libs()
        self.assertTrue(os.path.isdir(os.path.join(dummy1, ".git")))
        self.assertTrue(os.path.isdir(os.path.join(dummy2, ".git")))
