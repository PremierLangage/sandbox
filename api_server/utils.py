#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time
import tempfile
import tarfile
import os
import io

from hashlib import sha1
from typing import AnyStr, Tuple

from rest_framework.request import Request

from .models import FrozenResource
from .components import components_source
from .enums import LoaderErrCode

def data_to_hash(data: dict) -> str:
    """
        Hash a data with sha1.

        :param data: data to hash
    """
    return sha1(str(data).encode()).hexdigest() 

def tar_from_dic(files: dict) -> AnyStr:
    """
        Returns binaries of a tar gz file with the given file dictionnary
        Each entry of files is: "file_name": "file_content".

        :param files: dict of files and their content
    """
    with tempfile.TemporaryDirectory() as tmp_dir, tempfile.TemporaryDirectory() as env_dir:
        with tarfile.open(tmp_dir + "/environment.tgz", "w:gz") as tar:
            for key in files:
                with open(os.path.join(env_dir, key), "w") as f:
                    print(files[key], file=f)
            
            tar.add(env_dir, arcname=os.path.sep)
        
        with open(tmp_dir + "/environment.tgz", 'rb') as tar:
            tar_stream = tar.read()
    
    return tar_stream

def create_seed() -> int:
    """
        Creates a seed between 0 and 99
    """
    return int(time.time() % 100)

def build_pl(pl_data: dict, settings: dict = None, params: dict = None):
    if params is not None:
        pl_data = pl_data.update(params)

    if settings is not None:
        pl_data = pl_data.update(settings)

    if "seed" not in pl_data:
        pl_data["seed"] = create_seed()

def build_env(pl_data: dict, answer: dict = None) -> AnyStr:
    """
        Creates the environment to execute the builder or the grader
        on the sandbox.

        :param pl_data:     The content of pl
        :param answer:      The answer send by the client
    """
    env = dict(pl_data['__files'])
    env["components.py"] = components_source()
    
    tmp = dict(pl_data)
    del tmp['__files']
    env['pl.json'] = json.dumps(tmp)

    env['builder.sh'] = "#!/usr/bin/env bash\npython3 builder.py pl.json processed.json 2> stderr.log"
    env['grader.sh'] = "#!/usr/bin/env bash\npython3 grader.py pl.json answers.json processed.json feedback.html 2> stderr.log"
    
    if 'grader' in pl_data and 'grader.py' not in env:
        env['grader.py'] = pl_data['grader']
    
    if 'builder' in pl_data and 'builder.py' not in env:
        env['builder.py'] = pl_data['builder']
    
    if answer is not None:
        env['answer.json'] = json.dumps(answer)
    
    return tar_from_dic(env)

def build_config(list_commands: list, save: bool, environment: str=None, result_path: str=None) -> str:
    """
        Creates the configuration to execute in the sandbox.

        :param list_commands:   The list of commands to execute
        :param save:            True if the sandbox need to save the environment, False else
        :param environment:     Name of an existing environment to use
        :param result_path:     Path to a file in environment, where the content will be in the result
    """
    commands = {
        "commands": list_commands,
        "save": save,
        "environment": environment,
    }
    if result_path is not None:
        commands["result_path"] = result_path
    return json.dumps(commands)

def build_resource(data: dict, is_demo: bool, path: str):
    """
        Create resources to build in the sandbox.

        :param data:    data to send to sandbox
        :param is_demo: get data from a FrozenResource if False
    """

    if "answer" in data and "env_id" in data:
        return build_answer(data=data)
    
    env_id = data["env_id"] if "env_id" in data else None
    
    if not is_demo:
        if "resource_id" not in data:
            return LoaderErrCode.FROZEN_RESOURCE_ID_NOT_PRESENT, None
        try:
            frozen = FrozenResource.objects.get(id=int(data["resource_id"]))
            data = frozen.data
        except:
            return LoaderErrCode.FROZEN_RESOURCE_ID_NOT_IN_DB, None

    build_pl(data)
    env = build_env(data)
    if path is not None and env_id is not None:
        print(f"PATH : {path}")
        print(f"TYPE : {type(path)}")
        env_id = os.path.join(path, env_id)

    config = build_config(['sh builder.sh'], True, environment=env_id, result_path="processed.json")

    return env, config

def build_answer(data: dict) -> Tuple[dict, dict]:
    """
        Create the answer to evaluate in the sandbox.

        :param data:    The data contains env_id and answer.
    """
    answer = data["answer"]
    env_id = data["env_id"]
    env = tar_from_dic({"answers.json":json.dumps(answer)})
    config = build_config(['sh grader.sh'], True, environment=env_id, result_path="feedback.html")

    return env, config


def build_request(request: Request, env: str, config: dict, path: str):
    request._request.FILES["environment"] = io.BytesIO(env)

    _mutable = request._request.POST._mutable
    request._request.POST._mutable = True
    request._request.POST["config"] = config
    request._request.POST["path"] = path
    request._request.POST._mutable = _mutable