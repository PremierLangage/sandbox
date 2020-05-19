# git.py
#
# Authors:
#   - Coumes Quentin <coumes.quentin@gmail.com>

import logging
import os
import subprocess

from django.conf import settings


logger = logging.getLogger(__name__)


def clone(alias: str, url: str) -> int:
    """Execute a 'git clone <url> <alias>' inside EXTERNAL_LIBRARIES_ROOT, returning the command's
    status code."""
    cwd = os.getcwd()
    try:
        os.chdir(settings.EXTERNAL_LIBRARIES_ROOT)
        cmd = f"GIT_TERMINAL_PROMPT=0 git clone {url} {alias}"
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = p.communicate()
        if p.returncode:
            logger.error(f"Could not clone the external lib '{url}' into '{alias}'\n"
                         f"stdout: {out.decode()}\nstderr: {err.decode()}")
        return p.returncode
    finally:
        os.chdir(cwd)


def pull(alias: str, url: str) -> int:
    """Execute a 'git pull <url> master' in the repository of the given alias inside
    EXTERNAL_LIBRARIES_ROOT returning the command's status code."""
    cwd = os.getcwd()
    try:
        os.chdir(os.path.join(settings.EXTERNAL_LIBRARIES_ROOT, alias))
        cmd = f"GIT_TERMINAL_PROMPT=0 git pull {url} master"
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = p.communicate()
        if p.returncode:
            logger.error(f"Could not pull the external lib '{url}' with alias '{alias}'\n"
                         f"stdout: {out.decode()}\nstderr: {err.decode()}")
        return p.returncode
    finally:
        os.chdir(cwd)
