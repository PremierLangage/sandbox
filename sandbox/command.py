# command.py
#

import logging
import time
from typing import List, Tuple

from django.conf import settings
from django_http_exceptions import HTTPExceptions
from docker.models.containers import Container
from wrapt_timeout_decorator import timeout
from sandbox import utils
from .enums import SandboxErrCode

logger = logging.getLogger(__name__)

class Command:
    """Use to wrap bash commands."""
    
    
    def __init__(self, command: str, timeout: float = settings.EXECUTE_TIMEOUT, environ=None):
        if environ is None:
            environ = {}
        if command.startswith("-"):
            self.command = command[1:]
            self.ignore_failure = True
        else:
            self.command = command
            self.ignore_failure = False
        self.environ = environ if environ is not None else {}
        self.timeout = timeout
    
    
    def __repr__(self):
        return f"<executor.Command '{self.command}' timeout={self.timeout}>"
    
    
    __str__ = __repr__
    
    
    @staticmethod
    def _check(d: dict) -> bool:
        """Returns True if <d> is a valid representation of a command, False otherwise.
        
        Check that:
            - 'command' is present and is a string.
            - if 'timeout' is present, it is either an integer or a float."""
        return all((
            'command' in d and isinstance(d["command"], str),
            "timeout" not in d or isinstance(d["timeout"], (int, float)),
        ))
    
    
    @classmethod
    def from_config(cls, config: dict) -> List['Command']:
        """Extract commands from the config dictionary, returning a list of Commands."""
        if 'commands' not in config:
            raise HTTPExceptions.BAD_REQUEST.with_content("Missing field 'commands' in config")
        
        if not isinstance(config["commands"], list):
            raise HTTPExceptions.BAD_REQUEST.with_content(
                f'commands must be a list, not {type(config["commands"])}'
            )
        
        environ = utils.parse_environ(config)
        if not config["commands"]:
            raise HTTPExceptions.BAD_REQUEST.with_content(f"Command list cannot be empty")
        
        commands = list()
        for c in config["commands"]:
            if isinstance(c, dict) and cls._check(c):
                commands.append(Command(environ=environ, **c))
            elif isinstance(c, str):
                commands.append(Command(c, environ=environ))
            else:
                raise HTTPExceptions.BAD_REQUEST.with_content(f"Command badly formatted : '{c}'")
        
        return commands
    
    
    def execute(self, container: Container) -> Tuple[bool, dict]:
        """Execute the command on the given container."""
        start = time.time()
        try:
            exec_run = timeout(
                self.timeout, use_signals=False
            )(container.exec_run)
            exit_code, output = exec_run(
                ["bash", "-c", self.command], environment=self.environ, demux=True)
            stdout, stderr = ("" if out is None else out.decode().strip() for out in output)
        except TimeoutError:
            exit_code = SandboxErrCode.TIMEOUT.value
            stdout = ""
            stderr = f"Command timed out after {self.timeout} seconds\n"
        except Exception:  # pragma: no cover
            logger.exception(f"An error occurred while executing the command '{self.command}'")
            exit_code = SandboxErrCode.UNKNOWN.value
            stdout = ""
            stderr = "An unknown error occurred on the sandbox\n"
        
        result = {
            "command":   self.command,
            "exit_code": exit_code,
            "stdout":    stdout,
            "stderr":    stderr,
            "time":      time.time() - start,
        }
        
        if exit_code < 0 and exit_code != SandboxErrCode.TIMEOUT.value:  # pragma: no cover
            status = False
        elif self.ignore_failure:
            status = True
        else:
            status = (exit_code == 0)
        
        return status, result