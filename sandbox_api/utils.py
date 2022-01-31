import json
import os
import shutil
from sandbox.containers import Sandbox
from sandbox_api.errors import LoaderError, MissingFile

from settings import DIRECTORIES_ROOT

# def copy_file_on_sandbox(sandbox: Sandbox, path: str) -> None:
#     """Copy the file on shared volume to sandbox environnement."""
#     if not os.path.isfile(os.path.join(DIRECTORIES_ROOT, path)):
#         raise MissingFile(f'<{path}> to include not present or not a valid path file')
#     path = path.split('/')
#     shutil.copyfile(
#         os.path.join(DIRECTORIES_ROOT, os.path.join(*path)), # Source
#         os.path.join(sandbox.envpath, os.path.join(*path[1:])) # Destination
#     )

def copy_file_on_sandbox(sandbox: Sandbox, src_path: str, exp_path: str) -> None:
    """Copy the file on shared volume to sandbox environnement."""
    src_path = os.path.join(DIRECTORIES_ROOT, src_path)
    exp_path = os.path.join(sandbox.envpath, exp_path)
    if not os.path.isfile(src_path):
        raise MissingFile(f'<{src_path}> to include not present or not a valid path file')
    shutil.copyfile(src_path, exp_path)

def copy_pl_json_on_sandbox(sandbox: Sandbox, pl_json: dict) -> None:
    path = os.path.join(sandbox.envpath, 'pl.json')
    try:
        with open(path, 'w+') as file:
            json.dump(pl_json, file, indent=4)
    except IOError as e:
        raise LoaderError('generation pl.json failled', list(str(e)))