# assetor.py
#


import logging
import os
import tarfile
import time
from datetime import timedelta
from typing import List, Optional

from django.conf import settings
from django.utils import timezone
from .command import Command
from .containers import Sandbox
from .enums import SandboxErrCode


logger = logging.getLogger(__name__)


class Assetor:
    """This class provide methods to execute bash commands."""
    
    
    def __init__(self, commands: List[Command], sandbox: Sandbox, asset: str,
                 result: str = None, save: bool = False):
        self.commands = commands
        self.sandbox = sandbox
        self.asset_path = asset
        self.result_path = result
        self.save = save
    
    
    def _move_env_to_container(self):
        """Send the tar to the Docker and untar it inside the Docker"""
        start = time.time()
        
        with tarfile.open(self.asset_path, "r:gz") as tar:
            tar.extractall(self.sandbox.envpath)
        
        logger.debug(f"Moving environment to container took : {time.time() - start} seconds")
    
    
    def _get_result(self) -> Optional[str]:
        """Return the content of /home/student/<path> if found, an empty string otherwise."""
        start = time.time()
        with open(os.path.join(self.sandbox.envpath, self.result_path), encoding="UTF-8") as f:
            content = f.read()
        logger.debug(f"Getting result from container took : {time.time() - start} seconds")
        return content
    
    
    def execute(self) -> dict:
        """Execute each commands in the container."""
        start = time.time()
        
        self._move_env_to_container()
        
        execution = list()
        timeout = settings.EXECUTE_TIMEOUT
        for command in self.commands:
            command.timeout = min(command.timeout, timeout)
            status, exec_result = command.execute(self.sandbox.container)
            execution.append(exec_result)
            if not status:
                status = exec_result["exit_code"]
                break
            timeout -= max(exec_result["time"], 0)
        else:
            status = 0
        
        result = None
        if self.result_path is not None:
            try:
                result = self._get_result()
            except FileNotFoundError:
                status = SandboxErrCode.RESULT_NOT_FOUND.value
            except UnicodeDecodeError:
                status = SandboxErrCode.RESULT_NOT_UTF8.value
        
        response = {
            "status":     status,
            "execution":  execution,
            "total_time": time.time() - start,
        }
        
        # if self.save:
        #     expire = timezone.now() + timedelta(seconds=settings.ENVIRONMENT_EXPIRATION)
        #     response["environment"] = self.env_uuid
        #     response["expire"] = expire.isoformat()
        #     # Remove the one used by the container as it will cause an error in extract_env if the
        #     # destination already exists.
        #     os.remove(self.asset_path)
        #     self.sandbox.extract_env(self.env_uuid)
        # else:
        #     os.remove(self.asset_path)
        os.remove(self.asset_path)
        
        if result is not None:
            response["result"] = result
        
        return response
