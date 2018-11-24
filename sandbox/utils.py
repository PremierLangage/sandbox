# coding: utf-8

import os
import shutil
import time

from django.conf import settings

import docker



def remove_outdated_env():
    """Remove every file of MEDIA_ROOT that are outdated according to DEL_ENV_AFTER
    and DEL_TEST_ENV_AFTER."""
    current_time = time.time()
    
    for f in os.listdir(settings.MEDIA_ROOT):
        path = os.path.join(settings.MEDIA_ROOT, f)
        creation_time = os.path.getctime(path)
        
        if f.startswith('_test'):
            if (current_time - creation_time) >= settings.DEL_TEST_ENV_AFTER:
                shutil.rmtree(path)
        else:
            if (current_time - creation_time) >= settings.DEL_ENV_AFTER:
                shutil.rmtree(path)



