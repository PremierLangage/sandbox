import inspect
import os
import shutil
import uuid

from django.test import Client, SimpleTestCase, override_settings
from docker.errors import DockerException

from .. import container


RESOURCES_ROOT = os.path.join(os.path.dirname(__file__), "resources")

TEST_DIR = os.path.join("/tmp/django_test/sandbox/", str(uuid.uuid4()))

ENV1 = "dae5f9a3-a911-4df4-82f8-b9343241ece5"
ENV2 = "e77f958e-4757-4e8f-89eb-21a0153d53d4"



def raises_docker_exception():
    raise DockerException



class EnvTestCase(SimpleTestCase):
    """Base classe for tests using ENVIRONMENT_ROOT.
    
    It allows to use, modify, create and delete environments without modifying
    'settings.ENVIRONMENT_ROOT' or 'sandbox/tests/resources'.
    
    Resources defined in 'sandbox/tests/resources' are available in the 'TEST_DIR' directory,
    which can be imported from this module and is equivalent to settings.ENVIRONMENT_ROOT. """
    
    
    def __new__(cls, *args, **kwargs):
        """Decorate each tests of child classes with
        'override_settings(ENVIRONMENT_ROOT=TEST_DIR)'"""
        instance = super().__new__(cls)
        
        for attr_name in dir(instance):
            attr = getattr(instance, attr_name)
            if inspect.ismethod(attr):
                setattr(instance, attr_name, override_settings(ENVIRONMENT_ROOT=TEST_DIR)(attr))
        
        return instance
    
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = Client()
    
    
    def setUp(self):
        super().setUp()
        shutil.copytree(RESOURCES_ROOT, TEST_DIR)
    
    
    def tearDown(self):
        super().tearDown()
        shutil.rmtree(TEST_DIR)



class SandboxTestCase(EnvTestCase):
    """Base test class using containers"""
    
    
    def tearDown(self):
        super().tearDown()
        for c in container.CONTAINERS:
            c.release()
