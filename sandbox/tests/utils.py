import inspect
import os
import shutil
import tarfile
import uuid

from django.test import Client, SimpleTestCase, override_settings
from docker.errors import DockerException

from .. import containers


RESOURCES_ROOT = os.path.join(os.path.dirname(__file__), "resources")
RESOURCES_ENV_ROOT = os.path.join(RESOURCES_ROOT, "envs")
RESOURCES_LIB_ROOT = os.path.join(RESOURCES_ROOT, "libs")

TEST_ENVIRONMENT_ROOT = os.path.join("/tmp/django_test/sandbox/", str(uuid.uuid4()))
TEST_EXTERNAL_LIBRARIES_ROOT = os.path.join("/tmp/django_test/sandbox/", str(uuid.uuid4()))

ENV1 = "dae5f9a3-a911-4df4-82f8-b9343241ece5"
ENV2 = "e77f958e-4757-4e8f-89eb-21a0153d53d4"



def raises_docker_exception():
    raise DockerException



class EnvTestCase(SimpleTestCase):
    """Base class for tests using ENVIRONMENT_ROOT.
    
    It allows to use, modify, create and delete environments without modifying
    'settings.ENVIRONMENT_ROOT' or 'sandbox/tests/resources/envs'.
    
    Resources defined in 'sandbox/tests/resources/envs' are available in the 'TEST_ENVIRONMENT_ROOT'
    directory, which can be imported from this module, or through settings.ENVIRONMENT_ROOT. """
    
    
    def __new__(cls, *args, **kwargs):
        """Decorate each tests of child classes with
        'override_settings(ENVIRONMENT_ROOT=TEST_ENVIRONMENT_ROOT)'"""
        instance = super().__new__(cls)
        
        for attr_name in dir(instance):
            attr = getattr(instance, attr_name)
            if inspect.ismethod(attr):
                setattr(instance, attr_name,
                        override_settings(ENVIRONMENT_ROOT=TEST_ENVIRONMENT_ROOT)(attr))
        
        return instance
    
    
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
        tarfile.open(os.path.join(TEST_ENVIRONMENT_ROOT, f"{self.uuid4}.tgz"), "x:gz").close()
        super().setUp()
    
    
    def tearDown(self):
        shutil.rmtree(TEST_ENVIRONMENT_ROOT)
        super().tearDown()



class LibTestCase(SimpleTestCase):
    """Base class for tests using EXTERNAL_LIBRARIES_ROOT.

    It allows to use, modify, create and delete libs without modifying
    'settings.EXTERNAL_LIBRARIES_ROOT' or 'sandbox/tests/resources/libs'.

    Resources defined in 'sandbox/tests/resources/libs' are available in the
    'TEST_EXTERNAL_LIBRARIES_ROOT' directory, which can be imported from this module, or through
    settings.EXTERNAL_LIBRARIES_ROOT."""
    
    
    def __new__(cls, *args, **kwargs):
        """Decorate each tests of child classes with
        'override_settings(ENVIRONMENT_ROOT=TEST_ENVIRONMENT_ROOT)'"""
        instance = super().__new__(cls)
        
        for attr_name in dir(instance):
            attr = getattr(instance, attr_name)
            if inspect.ismethod(attr):
                setattr(instance, attr_name, override_settings(
                    EXTERNAL_LIBRARIES_ROOT=TEST_EXTERNAL_LIBRARIES_ROOT
                )(attr))
        
        return instance
    
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = Client()
    
    
    @classmethod
    def tearDownClass(cls):
        if os.path.exists(TEST_EXTERNAL_LIBRARIES_ROOT):
            shutil.rmtree(TEST_EXTERNAL_LIBRARIES_ROOT)
        super().tearDownClass()
    
    
    def setUp(self):
        shutil.copytree(RESOURCES_LIB_ROOT, TEST_EXTERNAL_LIBRARIES_ROOT)
        super().setUp()
    
    
    def tearDown(self):
        shutil.rmtree(TEST_EXTERNAL_LIBRARIES_ROOT)
        super().tearDown()



class SandboxTestCase(LibTestCase, EnvTestCase):
    """Base test class using containers"""
    
    
    def tearDown(self):
        for c in containers.CONTAINERS:
            c.release()
        super().tearDown()
