# containers.py
#
# Authors:
#   - Coumes Quentin <coumes.quentin@gmail.com>


import logging
import os
import queue
import shutil
import tarfile
import time

import docker
from django.conf import settings
from django_http_exceptions import HTTPExceptions
from docker.errors import DockerException
from docker.models.containers import Container


logger = logging.getLogger(__name__)

CONTAINERS: "queue.Queue['Sandbox']"


def create_container(name: str) -> Container:
    """Create a container with the paramaters defined in settings.py."""
    return docker.from_env().containers.run(
        name=name,
        volumes={
            os.path.join(settings.DOCKER_VOLUME_HOST_BASEDIR, name): {
                "bind": "/home/docker",
                "mode": "rw",
            },
            settings.EXTERNAL_LIBRARIES_ROOT:                        {
                "bind": "/utils/libs/",
                "mode": "ro",
            },
        },
        **settings.DOCKER_PARAMETERS
    )


def purging_containers():
    """Delete running container created from DOCKER_PARAMETERS["image"]"""
    to_del = docker.from_env().containers.list(all=True, filters={
        "ancestor": settings.DOCKER_PARAMETERS["image"]
    })
    for c in to_del:
        try:
            c.remove(force=True)
            logger.info(f"Container {c.short_id} removed.")
        except DockerException:
            logger.exception(f"Could not remove container {c.short_id}.")
    
    # Purging any existing container environment.
    logger.info("Purging any existing container environment.")
    if os.path.isdir(settings.DOCKER_VOLUME_HOST_BASEDIR):  # pragma: no cover
        shutil.rmtree(settings.DOCKER_VOLUME_HOST_BASEDIR)


def initialise_containers():
    """Called by settings.py to initialize containers at server launch."""
    global CONTAINERS
    
    purging_containers()
    
    # Create containers.
    logger.info("Initializing containers.")
    
    i = 0
    CONTAINERS = queue.Queue(settings.DOCKER_COUNT)
    while not CONTAINERS.full():
        c = Sandbox(f"c{i}", i)
        CONTAINERS.put(c)
        logger.info(
            f"Container {c.container.short_id} ({i + 1}/{settings.DOCKER_COUNT}) initialized.")
        i += 1
    
    logger.info("Containers initialized.")


class Sandbox:
    """Wrap a docker's container."""
    
    
    def __init__(self, name, index):
        path = os.path.join(settings.DOCKER_VOLUME_HOST_BASEDIR, name)
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
        os.makedirs(path)
        
        self.name = name
        self.container = create_container(name)
        self.index = index
        self.used_since = 0
        self.to_delete = False
        self.envpath = os.path.join(settings.DOCKER_VOLUME_HOST_BASEDIR, self.name)
    
    
    @staticmethod
    def available() -> int:
        """Return the approximative number of available container."""
        return CONTAINERS.qsize()
    
    
    @staticmethod
    def acquire() -> 'Sandbox':
        """Try to acquire a container for <settings.WAIT_FOR_CONTAINER_DURATION> seconds.
        
        Raises HTTPExceptions.SERVICE_UNAVAILABLE if no container were available in time."""
        global CONTAINERS
        
        start = time.time()
        try:
            cw = CONTAINERS.get(timeout=settings.WAIT_FOR_CONTAINER_DURATION)
        except queue.Empty:
            logger.warning(f"Failed to acquire a container after {time.time() - start} seconds)")
            raise HTTPExceptions.SERVICE_UNAVAILABLE.with_content(
                "Sandbox overloaded, retry after a few seconds."
            )
        
        cw.available = False
        cw.used_since = time.time()
        logger.info(
            f"Acquired container '{cw.name}' of id '{cw.index}'"
            f"(took {time.time() - start} seconds)"
        )
        
        return cw
    
    
    def extract_env(self, envid):
        """Retrieve the environment from the container and write it
        to [settings.ENVIRONMENT_ROOT]/[envid].tgz"""
        path = os.path.join(settings.ENVIRONMENT_ROOT, f"{envid}.tgz")
        if os.path.isfile(path):
            os.remove(path)
        
        with tarfile.open(path, "w:gz") as tar:
            for name in os.listdir(self.envpath):
                tar.add(os.path.join(self.envpath, name), arcname=name)
    
    
    def reset(self):
        """Reset a given container by killing it and overwriting it's instance with
        a new one."""
        global CONTAINERS
        
        try:
            try:
                self.container.remove(force=True)
            except DockerException:
                logger.info(f"Could not remove container '{self.name}' of id '{self.index}'")
            
            self = Sandbox(f"c{self.index}", self.index)
            logger.info(f"Successfully restarted container '{self.name}' of id '{self.index}'")
            CONTAINERS.put(self, False)
        except DockerException:
            logger.exception(f"Error while restarting container '{self.name}' of id '{self.index}'")
    
    
    @classmethod
    def reset_all(cls):
        """Reset every containers of CONTAINERS."""
        initialise_containers()
    
    
    def release(self):
        """Release this container."""
        global CONTAINERS
        
        try:
            shutil.rmtree(self.envpath)
            os.makedirs(self.envpath)
            self.container.restart()
            CONTAINERS.put(self, False)
            logger.info(f"Released container '{self.name}' of id '{self.index}'")
        
        except DockerException:
            logger.info(f"Could not release container '{self.name}' of id '{self.index}'")
            self.reset()
        
        except Exception:
            logger.exception(f"Could not release container '{self.name}' of id '{self.index}'")
            self.reset()
