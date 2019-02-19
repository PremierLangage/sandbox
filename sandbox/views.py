#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Python [3.6]
#
#  Author: Coumes Quentin     Mail: qcoumes@etud.u-pem.fr
#  Created: 2017-07-30
#  Last Modified: 2017-09-30


import io
import json
import logging
import os
import tarfile
import threading
import time
import traceback
import uuid

from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.urls import reverse
from django.views.generic import View

from sandbox.container import ContainerWrapper
from sandbox.enums import SandboxErrCode
from sandbox.executor import Builder, Evaluator
from sandbox.utils import get_most_recent_env, remove_outdated_env


logger = logging.getLogger(__name__)



class VersionView(View):
    """Return the version of the sandbox."""
    
    
    def get(self, request):
        """Return the version of the sandbox."""
        logger.info("Version request received from '" + request.META['REMOTE_ADDR'] + "'")
        return HttpResponse('{"version": ' + settings.SANDBOX_VERSION + '}', status=200)



class EnvView(View):
    """Allow to download an environment for testings purpose."""
    
    
    def head(self, request, env):
        """Return HttpResponse200 if any environment containing <env> and a suffix are found,
        404 otherwise."""
        
        return HttpResponse(status=200 if get_most_recent_env(env) else 404)
    
    
    def get(self, request, env):
        """Return all found environments containing <env>, 404 if no environment could not be
        found."""
        logger.info("Env get request received from '" + request.META['REMOTE_ADDR']
                    + "' with ID '" + env + "'")
        
        entries = [
            os.path.join(settings.MEDIA_ROOT, e) for e in os.listdir(settings.MEDIA_ROOT)
            if env in e
        ]
        
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode="w|gz") as tar:
            for e in entries:
                tar.add(e, arcname=os.path.basename(e))
        
        response = HttpResponse(stream.getvalue())
        response['Content-Type'] = "application/gzip"
        response['Content-Disposition'] = ('attachment; filename=' + env + ".tgz")
        
        return response



class BuildView(View):
    """Build an environment with the content of request."""
    
    
    def post(self, request):
        """Build an environment with the content of request."""
        start = time.time()
        logger.info("Build request received from '" + request.META['REMOTE_ADDR'] + "'")
        
        threading.Thread(target=remove_outdated_env).start()
        
        env_uuid = uuid.uuid4()
        container = None
        test = request.POST.get('test', False)
        
        try:
            while True:
                container = ContainerWrapper.acquire()
                if container is not None:
                    logger.debug("Acquiring a docker took " + str(time.time() - start))
                    break
                
                time.sleep(0.1)
                if time.time() - start > settings.WAIT_FOR_CONTAINER_DURATION:
                    return HttpResponse("Sandbox overloaded", status=503)
            
            environment = request.FILES.get('environment.tgz')
            if not environment:
                return HttpResponseBadRequest("Missing the parameter 'environment.tgz'")
            
            envname = ("test_" if test else "") + str(env_uuid) + ".tgz"
            path = os.path.join(settings.MEDIA_ROOT, envname)
            with open(path, 'wb') as f:
                f.write(environment.read())
            del environment
            
            logger.debug("POST BUILD took " + str(time.time() - start))
            response = Builder(container, path).execute()
            logger.debug("Total build took " + str(time.time() - start)
                         + " | environment : " + str(env_uuid))
        
        except Exception:  # Unknown error
            response = {
                "id":          str(env_uuid),
                "sandbox_url": request.build_absolute_uri(reverse("sandbox:index")),
                "status":      SandboxErrCode.UNKNOWN,
                "stderr":      "",
                "context":     {},
                "sandboxerr":  "An unknown error occured:\n" + traceback.format_exc()
            }
            logger.exception("An unknown exception occured during build of env %s:" % str(env_uuid))
        
        finally:
            container.extract_env(str(env_uuid), "_built", test=test)
            threading.Thread(target=container.release).start()
        
        return HttpResponse(json.dumps(response), status=200)



class EvalView(View):
    """Evaluate an answer inside env."""
    
    
    def post(self, request, env):
        """Evaluate an answer inside env."""
        start = time.time()
        logger.info("Evaluate post request received from '" + request.META['REMOTE_ADDR'] + "'")
        
        threading.Thread(target=remove_outdated_env).start()
        
        container = None
        path = get_most_recent_env(env)
        if path is None:
            raise Http404("Environment with id '" + env + "' not found")
        test = request.POST.get('test', False)
        
        try:
            while time.time() - start < settings.WAIT_FOR_CONTAINER_DURATION:
                container = ContainerWrapper.acquire()
                if container is not None:
                    logger.debug("Acquiring a docker took " + str(time.time() - start))
                    break
                time.sleep(0.1)
            else:
                return HttpResponse("Sandbox overloaded, retry in few seconds.", status=503)
            
            answers = request.POST.get('answers')
            if not answers:
                return HttpResponseBadRequest("Missing parameter 'answers'")
            answers = json.loads(answers)
            
            logger.debug("POST EVAL TOOK " + str(time.time() - start))
            response = Evaluator(container, path, answers).execute()
            logger.debug("Total eval took " + str(time.time() - start))
        
        except Exception:  # Unknown error
            response = {
                "id":          env,
                "sandbox_url": request.build_absolute_uri(reverse("sandbox:index")),
                "status":      SandboxErrCode.UNKNOWN,
                "grade":       (-1),
                "stderr":      "",
                "feedback":    ("Execution of the evaluating script failed due to an unkwown error."
                                + " Please contact your teacher."),
                "context":     {},
                "sandboxerr":  "An unknown error occured:\n" + traceback.format_exc()
            }
            logger.exception("An unknown exception occured during eval of env %s:" % env)
        
        finally:
            container.extract_env(env, "_graded", test=test)
            threading.Thread(target=container.release).start()
        
        return HttpResponse(json.dumps(response), status=200)
