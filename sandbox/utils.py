# coding: utf-8

import os, time

from django.conf import settings


def remove_outdated_env():
    """Remove every file of MEDIA_ROOT (but 'README') that are outdate according to DEL_ENV_AFTER
    and DEL_TEST_ENV_AFTER."""
    current_time = time.time()
    normal_seconds = settings.DEL_ENV_AFTER * 86400
    test_seconds = settings.DEL_TEST_ENV_AFTER * 86400
    
    for f in os.listdir(settings.MEDIA_ROOT):
        if "README" in f:
            continue
        
        path = os.path.join(settings.MEDIA_ROOT, f)
        creation_time = os.path.getctime(path)
        
        if f.startswith('_test') and (current_time - creation_time) >= test_seconds:
            os.remove(path)
        elif not f.startswith('_test') and (current_time - creation_time) >= normal_seconds:
            os.remove(path)
