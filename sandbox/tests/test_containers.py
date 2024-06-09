# test_containers.py
#
# Authors:
#   - Coumes Quentin <coumes.quentin@gmail.com>

import inspect
import os
import shutil
import tarfile
import time
import uuid
from threading import Timer

from django.conf import settings
from django.test import override_settings, SimpleTestCase, Client

from .utils import SandboxTestCase, raises_docker_exception
from ..containers import Sandbox, SandboxUnavailable

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sandbox.settings")

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


@override_settings()
class EnvTestCase(SimpleTestCase):
    """Base class for tests using ENVIRONMENT_ROOT.

    It allows to use, modify, create and delete environments without modifying
    'settings.ENVIRONMENT_ROOT' or 'sandbox/tests/resources/envs'.

    Resources defined in 'sandbox/tests/resources/envs' are available in the 'TEST_ENVIRONMENT_ROOT'
    directory, which can be imported from this module, or through settings.ENVIRONMENT_ROOT.
    """

    def __new__(cls, *args, **kwargs):
        """Decorate each tests of child classes with
        'override_settings(ENVIRONMENT_ROOT=TEST_ENVIRONMENT_ROOT)'"""
        instance = super().__new__(cls)

        for attr_name in dir(instance):
            attr = getattr(instance, attr_name)
            if inspect.ismethod(attr):
                setattr(
                    instance,
                    attr_name,
                    override_settings(ENVIRONMENT_ROOT=TEST_ENVIRONMENT_ROOT)(attr),
                )

        return instance


@override_settings(ENVIRONMENT_ROOT=TEST_ENVIRONMENT_ROOT)
@override_settings(EXTERNAL_LIBRARIES_ROOT=TEST_EXTERNAL_LIBRARIES_ROOT)
class SandboxWrapperTestCase(SimpleTestCase):

    def test_0_initialise_container(self):
        # 'initialise_container' is ran by settings.py
        # self.assertEquals(settings.DOCKER_COUNT, Sandbox.available())
        pass

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = Client()
        cls.uuid4 = uuid.uuid4()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(TEST_ENVIRONMENT_ROOT):
            shutil.rmtree(TEST_ENVIRONMENT_ROOT)
        super().tearDownClass()

    def setUp(self):
        shutil.copytree(RESOURCES_ENV_ROOT, TEST_ENVIRONMENT_ROOT)
        tarfile.open(
            os.path.join(TEST_ENVIRONMENT_ROOT, f"{self.uuid4}.tgz"), "x:gz"
        ).close()
        super().setUp()

    def tearDown(self):
        shutil.rmtree(TEST_ENVIRONMENT_ROOT)
        super().tearDown()

    # def test_acquire(self):
    #     Sandbox.acquire()
    #     self.assertEquals(settings.DOCKER_COUNT - 1, Sandbox.available())
    #
    # def test_acquire_wait_available(self):
    #     r = [Sandbox.acquire() for _ in range(settings.DOCKER_COUNT)].pop()
    #
    #     start = time.time()
    #     Timer(0.5, r.release).start()
    #     Sandbox.acquire()
    #     self.assertLessEqual(0.5, time.time() - start)
    #
    # @override_settings(WAIT_FOR_CONTAINER_DURATION=0.1)
    # def test_acquire_unavailable(self):
    #     for _ in range(settings.DOCKER_COUNT):
    #         Sandbox.acquire()
    #
    #     with self.assertRaises(SandboxUnavailable):
    #         Sandbox.acquire()
    #
    # def test_release(self):
    #     r = [Sandbox.acquire() for _ in range(settings.DOCKER_COUNT)].pop()
    #
    #     index = r.index
    #     r.release()
    #     r = Sandbox.acquire()
    #     self.assertEqual(index, r.index)
    #
    #     # Checking the container does work
    #     o = r.container.exec_run("true")
    #     self.assertEqual(0, o.exit_code)
    #
    # def test_reset(self):
    #     r = [Sandbox.acquire() for _ in range(settings.DOCKER_COUNT)].pop()
    #
    #     # Ensure r.release() will raise DockerException
    #     r.container.restart = raises_docker_exception
    #
    #     index = r.index
    #     r.release()
    #     r = Sandbox.acquire()
    #     self.assertEqual(index, r.index)
    #
    #     o = r.container.exec_run("true")
    #     self.assertEqual(0, o.exit_code)
    #
    # def test_extract_env(self):
    #     s = Sandbox.acquire()
    #     s.container.exec_run(["bash", "-c", 'echo "Hello World !" > world.txt'])
    #     path = os.path.join(settings.ENVIRONMENT_ROOT, "myenv.tgz")
    #     open(path, "w+").close()
    #
    #     s.extract_env("myenv")
    #
    #     with tarfile.open(path, "r:gz") as tar:
    #         self.assertEqual(b"Hello World !\n", tar.extractfile("world.txt").read())
