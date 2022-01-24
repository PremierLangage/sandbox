import os
import shutil
from pathlib import Path, PurePath
from django.http import (HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed,
                         HttpResponseNotFound, JsonResponse)

from sandbox.containers import Sandbox

from settings import DIRECTORIES_ROOT

def load_includes(loader: dict) -> list[str]:
    files = loader.get("include")
    
    if not isinstance(files, list):
        return HttpResponseBadRequest(f'include must be a list, not {type(loader)}')
    
    return files


def load_files(sandbox: Sandbox, files: list[str]):
    for path in files:
        if os.path.exists(os.path.join(DIRECTORIES_ROOT, path)):
            path = path.split('/')
            shutil.copyfile(
                os.path.join(DIRECTORIES_ROOT, os.path.join(*path)), # Source
                os.path.join(sandbox.envpath, os.path.join(*path[1:]))
            )
