# executor.py
#
# Authors:
#   - Coumes Quentin <coumes.quentin@gmail.com>


import logging
import os
import tarfile
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Tuple

from django.conf import settings
from django_http_exceptions import HTTPExceptions
from docker.models.containers import Container
from timeout_decorator import timeout_decorator

from sandbox.container import Sandbox
from sandbox.enums import SandboxErrCode


logger = logging.getLogger(__name__)



class Command:
    """Use to wrap bash commands."""
    
    
    def __init__(self, command: str, timeout: float = None):
        if command.startswith("-"):
            self.command = command[1:]
            self.ignore_failure = True
        else:
            self.command = command
            self.ignore_failure = False
        self.timeout = timeout
    
    
    @staticmethod
    def __check(d: dict) -> bool:
        """Returns True if <d> is a valid representation of a command else False.
        
        Check that:
            - 'command' is present and is a string.
            - if 'timeout' is present, it is either an integer or a float."""
        return (
                'command' in d and isinstance(d, str)
                and ("timeout" not in d or ("timeout" in d and isinstance(d["timeout"], (int, float))))
                and True
        )
    
    
    @classmethod
    def from_request(cls, config: dict) -> Tuple['Command', ...]:
        """Extract commands from the config dictionary, returning a list of Commands."""
        if 'commands' not in config:
            raise HTTPExceptions.BAD_REQUEST.with_response("Missing field 'commands' in config")
        
        commands = list()
        for c in config["commands"]:
            if isinstance(c, dict) and cls.__check(c):
                commands.append(Command(**c))
            elif isinstance(c, str):
                commands.append(Command(c))
            else:
                raise HTTPExceptions.BAD_REQUEST.with_response(f"Command badly formatted : '{c}'")
        
        return commands
    
    
    def execute(self, container: Container) -> Tuple[bool, dict]:
        """Execute the command on the given container."""
        start = time.time()
        
        try:
            if self.timeout is not None:
                exec_run = timeout_decorator.timeout(self.timeout, use_signals=False)(container.exec_run)
                exit_code, _ = exec_run(self.command)
            else:
                exit_code, _ = container.exec_run(self.command)
            
            stdout = container.logs(stdout=True, stderr=False, since=start)
            stderr = container.logs(stdout=False, stderr=True, since=start)
        except timeout_decorator.TimeoutError:
            exit_code = SandboxErrCode.TIMEOUT
            stdout = ""
            stderr = f"Sandbox timed out after {settings.EXECUTE_TIMEOUT} seconds"
        
        result = {
            "command":   self.command,
            "exit_code": exit_code,
            "stdout":    stdout,
            "stderr":    stderr,
            "time":      time.time() - start,
        }
        
        if exit_code < 0:
            status = False
        elif self.ignore_failure:
            status = True
        else:
            status = (exit_code == 0)
        
        return status, result



class Executor:
    """This class provide methods to execute bash commands."""
    
    
    def __init__(self, commands: Tuple[Command, ...], sandbox: Sandbox, env_uuid: str = None, envvars: dict = None,
                 result: str = None, save: bool = False):
        self.commands = commands
        self.sandbox = sandbox
        self.env_uuid = env_uuid
        self.env_path = os.path.join(settings.ENVIRONMENT_DIR, env_uuid) if env_uuid is not None else None
        self.envvars = envvars
        self.result_path = result
        self.save = save
    
    
    def __move_env_to_container(self):
        """Send the tar to the Docker and untar it inside the Docker"""
        start = time.time()
        
        with tarfile.open(self.env_path, "r:gz") as tar:
            tar.extractall(self.sandbox.envpath)
        
        logger.debug(f"Moving environment to container took : {time.time() - start} seconds")
    
    
    def __get_result(self) -> Optional[str]:
        """Return the content of /home/docker/<path> if found, an empty string otherwise."""
        start = time.time()
        
        try:
            with open(os.path.join(self.sandbox.envpath, self.result_path)) as f:
                content = f.read()
            return content
        except FileNotFoundError:
            return None
        finally:
            logger.debug(f"Getting result from container took : {time.time() - start} seconds")
    
    
    def __set_envvars(self):
        """Set environment variables inside the container."""
        start = time.time()
        self.sandbox.container.exec_run("export " + ' '.join([f"{k}={v}" for k, v in self.envvars.items()]))
        logger.debug(f"Setting environment variable inside the container took : {time.time() - start} seconds")
    
    
    def execute(self) -> dict:
        """Execute each commands in the container."""
        start = time.time()
        
        if self.env_path is not None:
            self.__move_env_to_container()
        
        self.__set_envvars()
        
        execution = list()
        
        for command in self.commands:
            status, exec_result = command.execute(self.sandbox.container)
            execution.append(exec_result)
            if not status:
                status = exec_result["exit_code"]
                break
        else:
            status = 0
        
        result = None
        if self.result_path is not None:
            result = self.__get_result()
            if result is None:
                status = SandboxErrCode.RESULT_NOT_FOUND
        
        response = {
            "status":     status,
            "execution":  execution,
            "total_time": time.time() - start,
        }
        
        if self.env_uuid is not None and self.save:
            response["environment"] = self.env_uuid
            response["expire"] = (datetime.now() + timedelta(seconds=settings.ENVIRONMENT_EXPIRATION)).isoformat()
            os.remove(self.env_path)
            threading.Thread(target=self.sandbox.extract_env, args=(self.env_uuid,))
        elif self.env_uuid is not None and not self.save:
            os.remove(self.env_path)
        
        if result is not None:
            response["result"] = result
        
        return response
