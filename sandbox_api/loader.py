from django.views.generic import View

from sandbox.containers import Sandbox
from sandbox.executor import Executor
from sandbox_api.errors import LoaderInstanceError

class Loader(View):
    
    def __init__(self, sandbox: Sandbox, loader: dict, config: dict):
        if not isinstance(loader, dict):
            raise LoaderInstanceError(
                f'loader must be a dict, not {type(loader)}',
                400
            )
        self.files = loader.get('include')
        if not isinstance(self.files, list[str]):
            raise LoaderInstanceError(
                f'include on loader must be a list[str], not {type(self.files)}',
                400
            )
        self.sandbox = sandbox
        self.loader = loader
        self.config = config
        
    def __build__(self):
        pass

    def __load__(self):
        pass

    def execute(self):
        pass




    


