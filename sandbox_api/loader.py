import json
from django.views.generic import View

from sandbox.containers import Sandbox
from sandbox.executor import Executor, Command
from sandbox_api.errors import LoaderContextError, LoaderError, LoaderInstanceError, LoaderSandboxError, WarningError
from sandbox_api.utils import copy_file_on_sandbox, copy_pl_json_on_sandbox
from sandbox import utils

class Loader(View):
    
    def __init__(self, sandbox: Sandbox, context: dict):
        """Loader need context of call
        
        Require loader -> json configuration
        Require config -> json configuration
        """

        self.warnings = list()

        if "loader" not in context:
            raise LoaderContextError('loader properties is missing as json')
        if "config" not in context:
            raise LoaderContextError('config properties is missing as json')

        try:
            self.loader = json.loads(context.get("loader"))
        except json.JSONDecodeError:
            raise LoaderInstanceError(f'loader must be a valid json')

        try:
            self.config = json.loads(context.get("config"))
        except json.JSONDecodeError:
            raise LoaderInstanceError(f'config must be a valid json')

        if sandbox is None:
            raise LoaderSandboxError('sandbox acquire probably failled')
        self.sandbox = sandbox
        
    def load_inclues(self) -> None:
        """Load and files on includes on sandbox environnement."""
        if "__includes" not in self.loader:
            raise LoaderInstanceError('Malforme meta information of file.')
        files = self.loader.get("__includes")
        if not isinstance(files, list):
            raise LoaderInstanceError(f'__includes must be list[str], but get {type(files)}')

        for file in files:
            try:
                copy_file_on_sandbox(self.sandbox, file['src_path'], file['exp_path'])
            except WarningError as warning:
                self.warnings.append(warning.dict())
        
    def load_pl_json(self):
        copy_pl_json_on_sandbox(self.sandbox, self.loader)

    def launch(self) -> None:
        self.load_inclues()
        if self.warnings:
            raise LoaderError("execute cannot continue with warnings", self.warnings)
        self.load_pl_json()

    def executor(self, sandbox: Sandbox, request) -> Executor:
        env = utils.executed_env(request, self.config)
        commands = Command.from_config(self.config)
        result_path = utils.parse_result_path(self.config)
        save = utils.parse_save(self.config)
        return Executor(commands, sandbox, env, result_path, save)






    


