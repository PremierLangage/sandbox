# test_containers.py
#
# Authors:
#   - Coumes Quentin <coumes.quentin@gmail.com>


import os
import tarfile
import time
from threading import Timer

from django.conf import settings
from django.test import override_settings
from django_http_exceptions import HTTPExceptions

from .utils import SandboxTestCase, raises_docker_exception
from ..containers import Sandbox



class SandboxWrapperTestCase(SandboxTestCase):
    
    def test_0_initialise_container(self):
        # 'initialise_container' is ran by settings.py
        self.assertEquals(settings.DOCKER_COUNT, Sandbox.count())
    
    
    def test_acquire(self):
        Sandbox.acquire()
        self.assertEquals(settings.DOCKER_COUNT - 1, Sandbox.available())
    
    
    def test_acquire_wait_available(self):
        r = [Sandbox.acquire() for _ in range(settings.DOCKER_COUNT)].pop()
        
        start = time.time()
        Timer(0.5, r.release).start()
        Sandbox.acquire()
        self.assertLessEqual(0.5, time.time() - start)
    
    
    @override_settings(WAIT_FOR_CONTAINER_DURATION=0.5)
    def test_acquire_unavailable(self):
        for _ in range(settings.DOCKER_COUNT):
            Sandbox.acquire()
        
        with self.assertRaises(HTTPExceptions.SERVICE_UNAVAILABLE):
            Sandbox.acquire()
    
    
    def test_release(self):
        r = [Sandbox.acquire() for _ in range(settings.DOCKER_COUNT)].pop()
        
        index = r.index
        r.release()
        r = Sandbox.acquire()
        self.assertEqual(index, r.index)
        
        # Checking the container does work
        o = r.container.exec_run("true")
        self.assertEqual(0, o.exit_code)
    
    
    def test_reset(self):
        r = [Sandbox.acquire() for _ in range(settings.DOCKER_COUNT)].pop()
        
        # Ensure r.release() will raise DockerException
        r.container.restart = raises_docker_exception
        
        index = r.index
        r.release()
        r = Sandbox.acquire()
        self.assertEqual(index, r.index)
        
        o = r.container.exec_run("true")
        self.assertEqual(0, o.exit_code)
    
    
    def test_extract_env(self):
        s = Sandbox.acquire()
        s.container.exec_run(["bash", "-c", 'echo "Hello World !" > world.txt'])
        path = os.path.join(settings.ENVIRONMENT_ROOT, "myenv.tgz")
        open(path, "w+").close()
        
        s.extract_env("myenv")
        
        with tarfile.open(path, "r:gz") as tar:
            self.assertEqual(b"Hello World !\n", tar.extractfile("world.txt").read())
