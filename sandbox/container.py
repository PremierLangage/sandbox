import logging
import os
import shutil
import threading
import time

import docker
from django.conf import settings


logger = logging.getLogger(__name__)

CONTAINERS = None



def create_container(name):
    return docker.from_env().containers.run(
        settings.DOCKER_IMAGE,
        detach=True,
        environment=settings.DOCKER_ENV_VAR,
        auto_remove=True,
        tty=True,
        cpuset_cpus=settings.DOCKER_CPUSET_CPUS,
        mem_limit=settings.DOCKER_MEM_LIMIT,
        memswap_limit=settings.DOCKER_MEMSWAP_LIMIT,
        name=name,
        volumes={
            os.path.join(settings.DOCKER_VOLUME_HOST, name): {
                "bind": settings.DOCKER_VOLUME_CONTAINER,
                "mode": "rw",
            },
        }
    )



class ContainerWrapper:
    """Wrap a docker container to store some data."""
    
    
    def __init__(self, name, index, available=True):
        self.name = name
        self.container = create_container(name)
        self.index = index
        self.available = available
        self.used_since = 0
        self.to_delete = False
        self.envpath = os.path.join(settings.DOCKER_VOLUME_HOST, self.name)
        self._get_default_file()
    
    
    def _reset(self):
        """Reset a given container by ensuring it's killed and overwriting it's instance with a new
        one."""
        global CONTAINERS
        
        try:
            try:
                self.container.kill()
            except docker.errors.DockerException:
                pass
            
            docker.from_env().containers.prune()
            
            cw = ContainerWrapper("c%d" % self.index, self.index)
            CONTAINERS[self.index] = cw
            
            logger.info(
                "Successfully restarted container '%s' of id '%d'" % (self.name, self.index))
        except docker.errors.DockerException:
            logger.exception(
                "Error while restarting container '%s' of id '%d'" % (self.name, self.index))
    
    
    def _get_default_file(self):
        """Copy every files and directory in DOCKER_DEFAULT_FILES into container environement."""
        for item in os.listdir(settings.DOCKER_DEFAULT_FILES):
            s = os.path.join(settings.DOCKER_DEFAULT_FILES, item)
            d = os.path.join(self.envpath, item)
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)
    
    
    @property
    def need_reset(self):
        """Return True if the container need to be reset, False otherwise."""
        return self.container.status not in ["running", "restarting", "created"] or self.to_delete
    
    
    @staticmethod
    def acquire():
        """Return the first available container, None if none were available."""
        global CONTAINERS
        
        cw = next((c for c in CONTAINERS if c.available), None)
        if cw is not None:
            CONTAINERS[cw.index].available = False
            CONTAINERS[cw.index].used_since = time.time()
            logger.info("Acquiring container '%s' of id '%d'" % (cw.name, cw.index))
        
        return cw
    
    
    def release(self):
        """Release this container."""
        global CONTAINERS
        
        if os.path.isdir(self.envpath):
            self.container.exec_run(["/bin/sh", "-c", "rm * -Rf"])
            shutil.rmtree(self.envpath)
        os.makedirs(self.envpath)
        self._get_default_file()
        self.container.restart()
        
        CONTAINERS[self.index].available = True
        logger.info("Releasing container '%s' of id '%d'" % (self.name, self.index))
    
    
    @classmethod
    def refresh_containers(cls):
        """Check that each container are either running, restarting or being created. Reset them if
        this is not the case."""
        global CONTAINERS
        
        for i in range(settings.DOCKER_COUNT):
            try:
                CONTAINERS[i].reload()
            except docker.errors.DockerException:
                CONTAINERS[i].to_delete = True
        
        for c in CONTAINERS:
            if not c.need_reset:
                continue
            
            logger.info("Restarting container '%s' of id '%d'" % (c.name, c.index))
            CONTAINERS[c.index].available = False
            threading.Thread(target=c._reset).start()



def initialise_container():
    """Called by settings.py to initialize containers at server launch."""
    global CONTAINERS
    
    time.sleep(0.5)
    # Kill stopped container created from DOCKER_IMAGE
    logger.info("Purging existing containers using image : %s." % settings.DOCKER_IMAGE)
    logger.info("Killed stopped container : %s." % str(docker.from_env().containers.prune()))
    # Kill running container created from DOCKER_IMAGE
    for c in docker.from_env().containers.list({"ancestor": settings.DOCKER_IMAGE}):
        logger.info("Killing container %s." % repr(c))
        c.kill()
        logger.info("Container %s killed." % repr(c))
    
    # Purging any existing container environment.
    logger.info("Purging any existing container environment.")
    if os.path.isdir(settings.DOCKER_VOLUME_HOST):
        shutil.rmtree(settings.DOCKER_VOLUME_HOST)
    
    logger.info("Creating new containers environment.")
    [os.makedirs(os.path.join(settings.DOCKER_VOLUME_HOST, "c%d" % i)) for i in
     range(settings.DOCKER_COUNT)]
    
    # Create containers.
    logger.info("Initializing containers.")
    CONTAINERS = []
    for i in range(settings.DOCKER_COUNT):
        CONTAINERS.append(ContainerWrapper("c%d" % i, i))
        logger.info("Container %d/%d initialized." % (i, settings.DOCKER_COUNT))
    logger.info("Containers initialized.")
