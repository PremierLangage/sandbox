from hashlib import sha224
from typing import AnyStr

from .components import components_source

import json
import tempfile
import tarfile
import os

def data_to_hash(data: dict):
    return sha224(str(data).encode()).hexdigest() 


def tar_from_dic(files: dict) -> AnyStr:
    """Returns binaries of a tar gz file with the given file dictionnary
    Each entry of files is: "file_name": "file_content"
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

def build_env(pl_data: dict, answer: dict = None) -> AnyStr:
        """Creates the environment to execute the builder or the grader
        on the sandbox.
        """
        env = dict(pl_data['__files'])
        env["components.py"] = components_source()
        
        tmp = dict(pl_data)
        del tmp['__files']
        env['pl.json'] = json.dumps(tmp)
        
        if 'grader' in pl_data and 'grader.py' not in env:
            env['grader.py'] = pl_data['grader']
        
        if 'builder' in pl_data and 'builder.py' not in env:
            env['builder.py'] = pl_data['builder']
        
        if answer is not None:
            env['answer.json'] = json.dumps(answer)
        
        return tar_from_dic(env)

def build_config(list_commands: list, save: bool, environment=None, result_path=None):
    commands = {
        "commands": list_commands,
        "save": save,
        "environment": environment,
    }
    if result_path is not None:
        commands["result_path"] = result_path
    return {
        "config": json.dumps(commands),
    }