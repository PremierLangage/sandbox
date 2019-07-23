import inspect
import os
import shutil
import uuid

from django.test import SimpleTestCase, override_settings


RESOURCES_ROOT = os.path.join(os.path.dirname(__file__), "resources")

TEST_DIR = os.path.join("/tmp/django_test/sandbox/", str(uuid.uuid4()))



class SandboxTestCase(SimpleTestCase):
    """Base classes for sandbox tests.
    
    It allows to use, modify, create and delete environments without modifying
    'settings.ENVIRONMENT_ROOT' or 'sandbox/tests/resources'.
    
    Resources defined in 'sandbox/tests/resources' are available in the 'TEST_DIR' directory,
    which can be imported from this module. """
    
    
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
        shutil.copytree(RESOURCES_ROOT, TEST_DIR)
    
    
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_DIR)
