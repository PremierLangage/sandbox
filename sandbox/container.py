# container.py
#
# Authors:
#   - Coumes Quentin <coumes.quentin@gmail.com>


import logging
import os
import shutil
import tarfile
import threading
import time

import docker
from django.conf import settings
from django_http_exceptions import HTTPExceptions
from docker.errors import DockerException
from docker.models.containers import Container


logger = logging.getLogger(__name__)

CONTAINERS = list()

LOCK = threading.Lock()



def create_container(name: str) -> Container:
    """Create a container with the paramaters defined in settings.py."""
    return docker.from_env().containers.run(
        name=name,
        volumes={
            os.path.join(settings.DOCKER_VOLUME_HOST_BASEDIR, name): {
                "bind": "/home/docker",
                "mode": "rw",
            },
        },
        **settings.DOCKER_PARAMETERS
    )



def initialise_container():
    """Called by settings.py to initialize containers at server launch."""
    global CONTAINERS
    
    CONTAINERS = list()
    
    # Deleting running container created from DOCKER_PARAMETERS["image"]
    to_del = docker.from_env().containers.list(all=True, filters={
        "ancestor": settings.DOCKER_PARAMETERS["image"]
    })
    for c in to_del:
        c.remove(force=True)
        logger.info(f"Container {c.short_id} removed.")
    
    # Purging any existing container environment.
    logger.info("Purging any existing container environment.")
    if os.path.isdir(settings.DOCKER_VOLUME_HOST_BASEDIR):  # pragma: no cover
        shutil.rmtree(settings.DOCKER_VOLUME_HOST_BASEDIR)
    
    # Create containers.
    logger.info("Initializing containers.")
    for i in range(settings.DOCKER_COUNT):
        c = Sandbox(f"c{i}", i)
        with LOCK:
            CONTAINERS.append(c)
        logger.info(f"Container {c.container.short_id} ({i}/{settings.DOCKER_COUNT}) initialized.")
    logger.info("Containers initialized.")



class Sandbox:
    """Wrap a docker's container."""
    
    
    def __init__(self, name, index, available=True):
        path = os.path.join(settings.DOCKER_VOLUME_HOST_BASEDIR, name)
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
        os.makedirs(path)
        
        self.name = name
        self.container = create_container(name)
        self.index = index
        self.available = available
        self.used_since = 0
        self.to_delete = False
        self.envpath = os.path.join(settings.DOCKER_VOLUME_HOST_BASEDIR, self.name)
        self.lock = threading.Lock()
    
    
    @staticmethod
    def _acquire() -> 'Sandbox':
        """Return the first available container, None if none were available."""
        global CONTAINERS
        
        LOCK.acquire()
        
        cw = next((c for c in CONTAINERS if c.available), None)
        if cw is not None:
            cw.available = False
            cw.used_since = time.time()
            logger.info(f"Acquiring container '{cw.name}' of id '{cw.index}'")
        
        LOCK.release()
        
        return cw
    
    
    @staticmethod
    def acquire() -> 'Sandbox':
        """Try to acquire a container for <settings.WAIT_FOR_CONTAINER_DURATION> seconds.
        
        Raises HTTPExceptions.SERVICE_UNAVAILABLE if no container were available in time."""
        start = time.time()
        while True:
            container = Sandbox._acquire()
            if container is not None:
                logger.debug(f"Acquiring a docker took {time.time() - start} secondes")
                break
            time.sleep(0.1)
            if time.time() - start >= settings.WAIT_FOR_CONTAINER_DURATION:
                raise HTTPExceptions.SERVICE_UNAVAILABLE.with_content(
                    "Sandbox overloaded, retry after a few secondes."
                )
        
        return container
    
    
    @staticmethod
    def count() -> int:
        """Return the number of available container."""
        global CONTAINERS
        
        return len(CONTAINERS)
    
    
    @staticmethod
    def available() -> int:
        """Return the number of available container."""
        global CONTAINERS
        
        with LOCK:
            count = len([c for c in CONTAINERS if c.available])
        
        return count
    
    
    def extract_env(self, envid):
        """Retrieve the environment from the container and write it
        to [settings.ENVIRONMENT_ROOT]/[envid].tgz"""
        self.lock.acquire()
        
        path = os.path.join(settings.ENVIRONMENT_ROOT, f"{envid}.tgz")
        if os.path.isfile(path):
            os.remove(path)
        
        with tarfile.open(path, "w:gz") as tar:
            for name in os.listdir(self.envpath):
                tar.add(os.path.join(self.envpath, name), arcname=name)
        
        self.lock.release()
    
    
    def _reset(self):
        """Reset a given container by killing it and overwriting it's instance with
        a new one."""
        global CONTAINERS
        
        try:
            try:
                self.container.remove(force=True)
            except DockerException:  # pragma: no cover
                logger.info("Could not remove container")
            
            self = Sandbox(f"c{self.index}", self.index)
            with LOCK:
                CONTAINERS[self.index] = self
            logger.info(f"Successfully restarted container '{self.name}' of id '{self.index}'")
        
        except DockerException:  # pragma: no cover
            logger.exception(f"Error while restarting container '{self.name}' of id '{self.index}'")
    
    
    def release(self):
        """Release this container."""
        global CONTAINERS
        
        if self.available:
            return
        
        self.lock.acquire()
        
        try:
            shutil.rmtree(self.envpath)
            os.makedirs(self.envpath)
            self.container.restart()
            self.available = True
            logger.info(f"Releasing container '{self.name}' of id '{self.index}'")
        
        except docker.errors.DockerException:
            logger.info(f"Could not release container '{self.name}' of id '{self.index}'")
            self._reset()
        
        self.lock.release()
