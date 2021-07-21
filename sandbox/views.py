# views.py
#
# Authors:
#   - Coumes Quentin <coumes.quentin@gmail.com>


import json
import logging
import os
import threading
import time
from io import SEEK_END

import docker
from django.conf import settings
from django.http import (HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed,
                         HttpResponseNotFound, JsonResponse)
from django.views.generic import View

from . import utils
from .containers import Sandbox
from .executor import Command, Executor


logger = logging.getLogger(__name__)


class EnvView(View):
    """Handle environment download."""
    
    
    def head(self, request, env):
        """Returns a response with status 200 if the environment <env> exists, 404 otherwise."""
        path_env = request.GET.get("path_env")
        if path_env is not None:
            env = os.path.join(path_env, str(env))

        path = utils.get_env(env)
        if path is None:
            return HttpResponseNotFound(f"No environment with UUID '{env}' found")
        
        response = HttpResponse()
        response["Content-Length"] = os.stat(path).st_size
        response['Content-Type'] = "application/gzip"
        response['Content-Disposition'] = f"attachment; filename={env}.tgz"
        return response
    
    
    def get(self, request, env):
        """Return the environment with the UUID <env>, 404 if it does not exists."""
        path_env = request.GET.get("path_env")
        if path_env is not None:
            env = os.path.join(path_env, str(env))

        path = utils.get_env(env)
        if path is None:
            return HttpResponseNotFound(f"No environment with UUID '{env}' found")
        
        with open(path, "rb") as f:
            response = HttpResponse(f.read())

        response["Content-Length"] = os.stat(path).st_size
        response['Content-Type'] = "application/gzip"
        response['Content-Disposition'] = f"attachment; filename={env}.tgz"
        return response


class FileView(View):
    """Handle environment's file download."""
    
    
    def head(self, request, env, path):
        """Returns a response with status 200 if <path> point to a file the environment <env>,
        404 otherwise."""
        path_env = request.GET.get("path_env")
        if path_env is not None:
            env = os.path.join(path_env, str(env))
        file = utils.extract(env, path)
        response = HttpResponse()
        response["Content-Length"] = file.seek(0, SEEK_END)
        response['Content-Type'] = "application/octet-stream"
        response['Content-Disposition'] = ('attachment; filename=' + os.path.basename(path))
        return response
    
    
    def get(self, request, env, path):
        """Returns a response with status 200 if <path> point to a file the environment <env>,
        404 otherwise."""
        path_env = request.GET.get("path_env")
        if path_env is not None:
            env = os.path.join(path_env, str(env))
        file = utils.extract(env, path)
        response = HttpResponse(file.read())
        response["Content-Length"] = file.tell()
        response['Content-Type'] = "application/octet-stream"
        response['Content-Disposition'] = ('attachment; filename=' + os.path.basename(path))
        return response


class SpecificationsView(View):
    
    def get(self, _):
        """Returns the specs of the sandbox."""
        return JsonResponse(utils.specifications())


class UsageView(View):
    
    def get(self, _):
        """Returns the usage of the sandbox."""
        return JsonResponse(utils.usage())


class LibrariesView(View):
    
    def get(self, _):
        """Returns the libraries installed on the containers."""
        response = docker.from_env().containers.run(
            settings.DOCKER_PARAMETERS["image"], "python3 /utils/libraries.py"
        )
        return JsonResponse(json.loads(response))


class ExecuteView(View):
    
    def post(self, request):
        """Allows to execute bash commands within an optional environment."""
        start = time.time()
        
        config = request.POST.get("config")
        if config is None:
            return HttpResponseBadRequest("Missing argument 'config'")
        
        try:
            config = json.loads(config)
            if not isinstance(config, dict):
                return HttpResponseBadRequest(f'config must be an object, not {type(config)}')
        except json.JSONDecodeError as e:
            return HttpResponseBadRequest(f"'config' json is invalid - {e}")
        
        env = utils.executed_env(request, config)
        commands = Command.from_config(config)
        result_path = utils.parse_result_path(config)
        save = utils.parse_save(config)
        
        logger.debug(f"Parsing config request took : {time.time() - start} seconds")
        
        sandbox = Sandbox.acquire()
        try:
            response = Executor(commands, sandbox, env, result_path, save).execute()
            logger.debug(f"Total execute request took : {time.time() - start} seconds")
            return JsonResponse(response)
        finally:
            threading.Thread(target=sandbox.release).start()
