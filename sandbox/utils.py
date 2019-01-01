# coding: utf-8

import os
import tarfile
import time

from django.conf import settings



def remove_outdated_env():
    """Remove every file of MEDIA_ROOT that are outdated according to DEL_ENV_AFTER
    and DEL_TEST_ENV_AFTER."""
    current_time = time.time()
    
    for f in os.listdir(settings.MEDIA_ROOT):
        path = os.path.join(settings.MEDIA_ROOT, f)
        creation_time = os.path.getctime(path)
        
        if f.startswith('_test'):
            if (current_time - creation_time) >= settings.DEL_TEST_ENV_AFTER:
                os.remove(path)
        else:
            if (current_time - creation_time) >= settings.DEL_ENV_AFTER:
                os.remove(path)



def get_env_from_docker(cw, envpath, suffix):
    """Retrieve the environment from the docker and write it to envpath."""
    path, ext = os.path.splitext(os.path.basename(envpath))
    path = os.path.join(settings.MEDIA_ROOT, path + suffix + ext)

    with tarfile.open(path, "w|gz") as tar:
        for name in os.listdir(cw.envpath):
            tar.add(os.path.join(cw.envpath, name), arcname=name)




def get_env_and_reset(cw, envpath, suffix):
    if cw is not None:
        get_env_from_docker(cw, envpath, suffix)
        cw.release()
