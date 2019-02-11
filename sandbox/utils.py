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



def get_most_recent_env(envid):
    """Returns the path to the most recent environment's tar whose name contains <envid> and any
    suffix, return None if no such tar was found."""
    
    
    def mtime(entry):
        """Return the modified time of <entry> in se ttings.MEDIA_ROOT."""
        return os.stat(entry).st_mtime
    
    entries = [os.path.join(settings.MEDIA_ROOT, e) for e in os.listdir(settings.MEDIA_ROOT)]
    envs = [e for e in entries if envid in e and not os.path.splitext(e)[0].endswith(envid)]
    
    return max(envs, key=mtime) if envs else None
