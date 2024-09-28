import os
import shutil
import tarfile

import uuid

from django.test import Client, TestCase, override_settings
from docker.errors import DockerException
from sandbox.containers import initialise_containers, purging_containers


RESOURCES_ROOT = os.path.join(os.path.dirname(__file__), "resources")
RESOURCES_ENV_ROOT = os.path.join(RESOURCES_ROOT, "envs")
RESOURCES_LIB_ROOT = os.path.join(RESOURCES_ROOT, "libs")


TEST_ENVIRONMENT_ROOT = os.path.join("/tmp/django_test/sandbox/", str(uuid.uuid4()))
TEST_EXTERNAL_LIBRARIES_ROOT = os.path.join(
    "/tmp/django_test/sandbox/", str(uuid.uuid4())
)

ENV1 = "dae5f9a3-a911-4df4-82f8-b9343241ece5"
ENV2 = "e77f958e-4757-4e8f-89eb-21a0153d53d4"

DUMMY_GIT_URL = "https://github.com/github/practice"


@override_settings(
    EXTERNAL_LIBRARIES_ROOT=TEST_EXTERNAL_LIBRARIES_ROOT,
    ENVIRONMENT_ROOT=TEST_ENVIRONMENT_ROOT,
)
class SandboxTestCase(TestCase):
    @staticmethod
    def remove_test_folders():
        if os.path.exists(TEST_EXTERNAL_LIBRARIES_ROOT):
            shutil.rmtree(TEST_EXTERNAL_LIBRARIES_ROOT)
        if os.path.exists(TEST_ENVIRONMENT_ROOT):
            shutil.rmtree(TEST_ENVIRONMENT_ROOT)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = Client()
        cls.uuid4 = uuid.uuid4()

    @classmethod
    def tearDownClass(cls):
        cls.remove_test_folders()

        super().tearDownClass()

    def setUp(self):
        shutil.copytree(RESOURCES_LIB_ROOT, TEST_EXTERNAL_LIBRARIES_ROOT)
        shutil.copytree(RESOURCES_ENV_ROOT, TEST_ENVIRONMENT_ROOT)
        tarfile.open(
            os.path.join(TEST_ENVIRONMENT_ROOT, f"{self.uuid4}.tgz"), "x:gz"
        ).close()
        initialise_containers()

        super().setUp()

    def tearDown(self):
        self.remove_test_folders()
        purging_containers()
        super().tearDown()


def raises_docker_exception():
    raise DockerException
