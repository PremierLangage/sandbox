# tasks.py
#
# Authors:
#   - Coumes Quentin <coumes.quentin@gmail.com>


import logging
import os
import shutil
import time

from django.conf import settings

from sandbox.utils import clone, pull


logger = logging.getLogger(__name__)



def refresh_external_libs():
    """Update external libs by cloning/pulling them."""
    for url, alias in settings.EXTERNAL_LIBRARIES:
        path = os.path.join(settings.EXTERNAL_LIBRARIES_ROOT, alias)
        if os.path.exists(path):
            pull(alias, url)
            logger.info(f"Library '{alias}' updated from '{url}.")
        else:
            clone(alias, url)
            logger.info(f"Library '{alias}' cloned from '{url}.")



def remove_expired_env():
    """Remove every file of MEDIA_ROOT that are expired according to ENVIRONMENT_EXPIRATION."""
    current_time = time.time()
    
    for f in os.listdir(settings.ENVIRONMENT_ROOT):
        path = os.path.join(settings.ENVIRONMENT_ROOT, f)
        creation_time = os.path.getctime(path)
        
        if (current_time - creation_time) >= settings.ENVIRONMENT_EXPIRATION:
            os.remove(path) if os.path.isfile(path) else shutil.rmtree(path)
            logger.info(f"environment {f} has expired and has been deleted.")
