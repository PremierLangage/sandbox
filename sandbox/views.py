# views.py
#
# Authors:
#   - Coumes Quentin <coumes.quentin@gmail.com>


import json
import logging
import os
import re
import subprocess
import threading
import time
from io import SEEK_END

import docker
from django.conf import settings
from django.http import (HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed, HttpResponseNotFound,
                         JsonResponse)
from django.views.generic import View

from . import utils
from .container import Sandbox
from .executor import Command, Executor


logger = logging.getLogger(__name__)



class EnvView(View):
    """Handle environment download."""
    
    
    def head(self, _, env):
        """Returns a response with status 200 if the environment <env> exists, 404 otherwise."""
        path = utils.get_env(env)
        if path is None:
            return HttpResponseNotFound(f"No environment with UUID '{env}' found")
        
        response = HttpResponse()
        response["Content-Length"] = os.stat(path).st_size
        response['Content-Type'] = "application/gzip"
        response['Content-Disposition'] = ('attachment; filename=' + env + ".tgz")
        return response
    
    
    def get(self, _, env):
        """Return the environment with the UUID <env>, 404 if it does not exists."""
        path = utils.get_env(env)
        if path is None:
            return HttpResponseNotFound(f"No environment with UUID '{env}' found")
        
        with open(path, "rb") as f:
            response = HttpResponse(f.read())
        
        response["Content-Length"] = os.stat(path).st_size
        response['Content-Type'] = "application/gzip"
        response['Content-Disposition'] = ('attachment; filename=' + env + ".tgz")
        return response



class FileView(View):
    """Handle environment's file download."""
    
    
    def head(self, _, env, path):
        """Returns a response with status 200 if <path> point to a file the environment <env>,
        404 otherwise."""
        file = utils.extract(env, path)
        response = HttpResponse()
        response["Content-Length"] = file.seek(0, SEEK_END)
        response['Content-Type'] = "application/octet-stream"
        response['Content-Disposition'] = ('attachment; filename=' + os.path.basename(path))
        return response
    
    
    def get(self, _, env, path):
        """Returns a response with status 200 if <path> point to a file the environment <env>,
        404 otherwise."""
        file = utils.extract(env, path)
        response = HttpResponse(file.read())
        response["Content-Length"] = file.tell()
        response['Content-Type'] = "application/octet-stream"
        response['Content-Disposition'] = ('attachment; filename=' + os.path.basename(path))
        return response



def specifications(request):
    """Returns the specs of the sandbox."""
    if request.method != "GET":
        return HttpResponseNotAllowed(['GET'], f"405 Method Not Allowed : {request.method}")
    
    cpu_count = settings.DOCKER_PARAMETERS["cpuset_cpus"]
    if "-" in cpu_count:
        lower, upper = cpu_count.split("-")
        cpu_count = upper - lower + 1
    else:
        cpu_count = len(cpu_count.split(","))
    
    infos = subprocess.check_output("cat /proc/cpuinfo", shell=True, universal_newlines=True)
    for line in infos.strip().split("\n"):
        if "model name" in line:
            cpu_name = re.sub(r"\s*model name\s*:", "", line, 1).strip()
            break
    else:
        cpu_name = ""
    
    available = Sandbox.available()
    docker_version = subprocess.check_output("docker -v", shell=True, universal_newlines=True)
    docker_version = docker_version.strip()[15:].split(",")[0]
    
    if ("storage_opt" in settings.DOCKER_PARAMETERS
            and "size" in settings.DOCKER_PARAMETERS["storage_opt"]):
        storage = settings.DOCKER_PARAMETERS["storage_opt"]["size"]
    else:
        storage = "host"
    
    response = {
        "containers":      {
            "total":     settings.DOCKER_COUNT,
            "running":   settings.DOCKER_COUNT - available,
            "available": available,
        },
        "envvar":          settings.DOCKER_PARAMETERS["environment"],
        "cpu":             {
            "count":  cpu_count,
            "period": settings.DOCKER_PARAMETERS["cpu_period"],
            "shares": settings.DOCKER_PARAMETERS["cpu_shares"],
            "quota":  settings.DOCKER_PARAMETERS["cpu_quota"],
            "name":   cpu_name,
        },
        "memory":          {
            "limit":   settings.DOCKER_PARAMETERS["mem_limit"],
            "swap":    settings.DOCKER_PARAMETERS["memswap_limit"],
            "storage": storage,
        },
        "docker_version":  docker_version,
        "sandbox_version": settings.SANDBOX_VERSION,
        "execute_timeout": settings.EXECUTE_TIMEOUT,
        "expiration":      settings.ENVIRONMENT_EXPIRATION,
    }
    
    return JsonResponse(response)



def libraries(request):
    if request.method != "GET":
        return HttpResponseNotAllowed(['GET'], f"405 Method Not Allowed : {request.method}")
    
    response = docker.from_env().containers.run(settings.DOCKER_PARAMETERS["image"], "python3 /utils/libraries.py")
    return JsonResponse(json.loads(response))



def execute(request):
    """Allows to execute bash commands within an optionnal environment."""
    if request.method != "POST":
        return HttpResponseNotAllowed(['POST'], f"405 Method Not Allowed : {request.method}")
    
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
    commands = Command.from_request(config)
    envvars = utils.parse_envvars(config)
    result_path = utils.parse_result_path(config)
    save = utils.parse_save(config)
    
    logger.debug(f"Parsing config request took : {time.time() - start} seconds")
    
    sandbox = Sandbox.acquire()
    
    response = Executor(commands, sandbox, env, envvars, result_path, save).execute()
    threading.Thread(target=sandbox.release)
    
    logger.debug(f"Total execute request took : {time.time() - start} seconds")
    
    return JsonResponse(response)
