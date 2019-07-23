# utils.py
#
# Authors:
#   - Coumes Quentin <coumes.quentin@gmail.com>


import io
import os
import tarfile
import uuid
from typing import BinaryIO, Optional

from django.conf import settings
from django.http import HttpRequest
from django_http_exceptions import HTTPExceptions



def merge_tar_gz(a: Optional[BinaryIO], b: Optional[BinaryIO]) -> Optional[BinaryIO]:
    """Merge <a> and <b>, returning a new tarfile.TarFile object.

    If two files in <a> and <b> have the same name, the one in <a> prevails.
    
    Both a and b can be safely closed after this function.
    
    Returns
        None       - If both arguments are None.
        a          - If <b> is None.
        b          - If <a> is None.
        io.BytesIO - A BytesIO, cursor set at the start, corresponding to the
                     merging of <a> into <b> (overwriting file with the same
                     name)."""
    if a is None:
        return None if b is None else io.BytesIO(b.read())
    if b is None:
        return io.BytesIO(a.read())
    
    destio = io.BytesIO()
    
    with tarfile.open(fileobj=a, mode="r:gz") as t1, \
            tarfile.open(fileobj=b, mode="r:gz") as t2, \
            tarfile.open(fileobj=destio, mode="w:gz") as dest:
        
        t1_members = [m for m in t1.getmembers()]
        t1_names = t1.getnames()
        t2_members = [m for m in t2.getmembers() if m.name not in t1_names]
        
        for member in t1_members:
            if member.isdir():
                dest.addfile(member)
            else:
                dest.addfile(member, t1.extractfile(member))
        
        for member in t2_members:
            if member.isdir():
                dest.addfile(member)
            else:
                dest.addfile(member, t2.extractfile(member))
    
    destio.seek(0)
    return destio



def get_env(env: str) -> Optional[str]:
    """Returns the path of the environment <env>, None if it does not exists."""
    path = os.path.join(settings.ENVIRONMENT_ROOT, env + ".tgz")
    return path if os.path.isfile(path) else None



def extract(env: str, path: str) -> Optional[BinaryIO]:
    """Extract and returns the file at <path> inside <env>, returns None of either the environment
    or the file could not be found."""
    env_path = get_env(env)
    if env_path is None:
        raise HTTPExceptions.NOT_FOUND.with_content(f"No environment with UUID '{env}' found")
    
    try:
        with tarfile.open(env_path, mode="r:gz") as tar:
            buffer = tar.extractfile(tar.getmember(path))
            file = io.BytesIO(buffer.read())
    except KeyError:
        raise HTTPExceptions.NOT_FOUND.with_content(
            f"The file '{path}' could not be found in environment '{env}'"
        )
    
    return file



def executed_env(request: HttpRequest, config: dict) -> Optional[str]:
    """Returns the UUID4 corresponding to the environment that will be used in the execution,
    will return None if no environment is needed.
    
    If an environment is provided both in the body and the config, this function will do the merge
    through 'merge_tar_gz()'.
    
    raises:
        - django_http_exceptions.HTTPExceptions.NOT_FOUND if the environment asked in request's
          config cannot be found.
    """
    body_env = request.FILES.get("environment")
    
    sandbox_env = None
    sandbox_env_uuid = config.get("environment")
    if sandbox_env_uuid is not None:
        sandbox_env = get_env(sandbox_env_uuid)
        if not sandbox_env:
            raise HTTPExceptions.NOT_FOUND.with_content(
                f"No environment with UUID '{sandbox_env_uuid}' found"
            )
        sandbox_env = open(sandbox_env, "rb")
    
    env = merge_tar_gz(body_env, sandbox_env)
    
    if body_env is not None:
        body_env.close()
    if sandbox_env is not None:
        sandbox_env.close()
    
    uuid_env = None
    if env is not None:
        uuid_env = str(uuid.uuid4())
        with open(os.path.join(settings.ENVIRONMENT_ROOT, uuid_env + ".tgz"), "w+b") as f:
            f.write(env.read())
    
    return uuid_env



def parse_envvars(config: dict) -> Optional[dict]:
    """Check the validity of 'envvars' in the request and return it, returns None if it is not
    present."""
    if "envvars" in config:
        if not isinstance(config["envvars"], dict):
            raise HTTPExceptions.BAD_REQUEST.with_content(
                f'envvars must be an object, not {type(config["envvars"])}')
        return {k: str(v) for k, v in config["envvars"].items()} if "envvars" in config else dict()
    return None



def parse_result_path(config: dict) -> Optional[str]:
    """Check the validity of 'result' in the request and return it, returns None if it is not
    present."""
    if "result_path" in config:
        if not isinstance(config["result_path"], str):
            raise HTTPExceptions.BAD_REQUEST.with_content(
                f'result_path must be a string, not {type(config["result_path"])}')
        return config["result_path"]
    return None



def parse_save(config: dict) -> bool:
    """Check the validity of 'save' in the request and return it, returns False if it is not
    present."""
    if "save" in config:
        if not isinstance(config["save"], bool):
            raise HTTPExceptions.BAD_REQUEST.with_content(
                f'save must be a boolean, not {type(config["save"])}')
        return config["save"]
    return False
