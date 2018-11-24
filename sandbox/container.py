import logging
import os
import shutil
import threading
import time

import docker
from django.conf import settings


logger = logging.getLogger(__name__)



class ContainerWrapper:
    """Wrap a docker container to store some data."""
    
    
    def __init__(self, name, index, available=True):
        self.name = name
        self.container = settings.CREATE_CONTAINER(name)
        self.index = index
        self.available = available
        self.used_since = 0
        self.to_delete = False
        self.envpath = os.path.join(settings.DOCKER_VOLUME_HOST, self.name)
        self._get_default_file()
    
    
    def _reset(self):
        """Reset a given container by ensuring it's killed and overwriting it's instance with a new
        one."""
        try:
            try:
                self.container.kill()
            except docker.errors.DockerException:
                pass
            
            docker.from_env().containers.prune()
            
            cw = ContainerWrapper("c%d" % self.index, self.index)
            settings.CONTAINERS[self.index] = cw
            
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
        cw = next((c for c in settings.CONTAINERS if c.available), None)
        if cw is not None:
            settings.CONTAINERS[cw.index].available = False
            settings.CONTAINERS[cw.index].used_since = time.time()
            logger.debug("Acquiring container '%s' of id '%d'" % (cw.name, cw.index))
        
        return cw
    
    
    def release(self):
        """Release this container."""
        if os.path.isdir(self.envpath):
            shutil.rmtree(self.envpath)
        os.makedirs(self.envpath)
        self._get_default_file()
        self.container.restart()
        
        settings.CONTAINERS[self.index].available = True
        logger.debug("Releasing container '%s' of id '%d'" % (self.name, self.index))
    
    
    @classmethod
    def refresh_containers(cls):
        """Check that each container are either running, restarting or being created. Reset them if
        this is not the case."""
        for i in range(settings.DOCKER_COUNT):
            try:
                settings.CONTAINERS[i].reload()
            except docker.errors.DockerException:
                settings.CONTAINERS[i].to_delete = True
        
        for c in settings.CONTAINERS:
            if not c.need_reset:
                continue
            
            logger.info("Restarting container '%s' of id '%d'" % (c.name, c.index))
            settings.CONTAINERS[c.index].available = False
            threading.Thread(target=c._reset).start()
