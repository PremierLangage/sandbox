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
    
    def __init__(self, commands: List[Command], sandbox: Sandbox,
                 path: str, export: str, result_path: str) -> None:
        self.commands = commands
        self.sandbox = sandbox
        self.path = path
        self.export = export
        self.result_path = result_path

    def _move_path_to_container(self):
        start = time.time()
        with tarfile.open(self.path, "r:gz") as tar:
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
        start = time.time()

        self._move_path_to_container()

        execution = list()
        timeout = settings.EXECUTE_TIMEOUT
        for command in self.commands:
            command.timeout = min(command.timeout, timeout)
            status, exec_result = command.execute(self.sandbox.container)
            execution.append(exec_result)
            if not status:
                status = exec_result['exit_code']
                break
            timeout -= max(exec_result['time'], 0)
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
            'status'    : status,
            'execution' : execution,
            'total_time': time.time() - start
        }

        if result is not None:
            response['result'] = result

        if not self.export:
            os.remove(self.path)
        else:
            self.sandbox.extract_environment(self.export)
        
        return response
