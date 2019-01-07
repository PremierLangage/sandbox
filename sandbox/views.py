#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Python [3.6]
#
#  Author: Coumes Quentin     Mail: qcoumes@etud.u-pem.fr
#  Created: 2017-07-30
#  Last Modified: 2017-09-30


import json
import logging
import os
import threading
import time
import traceback
import uuid
from distutils.version import StrictVersion

from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.urls import reverse
from django.views.generic import View

from sandbox.container import ContainerWrapper
from sandbox.enums import SandboxErrCode
from sandbox.executor import Builder, Evaluator
from sandbox.utils import get_env_and_reset, remove_outdated_env


logger = logging.getLogger(__name__)



class IndexView(View):
    
    def post(self, request):
        """Check wether the sandbox can execute a request according to the version."""
        logger.info("POST request received from '" + request.META['REMOTE_ADDR'] + "'")
        
        version = request.GET.POST('version')
        
        if not version:
            return HttpResponseBadRequest("Missing parameter 'version'")
        
        try:
            if StrictVersion(settings.SANDBOX_VERSION) < StrictVersion(version):
                return HttpResponse("Sandbox is out of date", status=406)
            if settings.SANDBOX_VERSION[0] != version[0]:
                return HttpResponse("Sandbox major revision (" + settings.SANDBOX_VERSION[0] + ") "
                                    + "differs from requested version (" + version[0] + ")",
                                    status=406)
        except ValueError:
            return HttpResponseBadRequest("'version' should take the form of MAJOR.MINOR.PATCH")
        
        return HttpResponse(status=204)



class VersionView(View):
    
    def get(self, request):
        """Return the version of the sandbox."""
        logger.info("Version request received from '" + request.META['REMOTE_ADDR'] + "'")
        return HttpResponse('{"version": ' + settings.SANDBOX_VERSION + '}', status=200)



class EnvView(View):
    """Allow to download an environment for testings purpose."""
    
    
    def get(self, request, env):
        """Return the environment, status 404 if the environment could not be found."""
        logger.info("Env get request received from '" + request.META['REMOTE_ADDR']
                    + "' with ID '" + env + "'")
        
        threading.Thread(target=remove_outdated_env).start()
        
        path = os.path.join(settings.MEDIA_ROOT, env + '_built.tgz')
        if not os.path.isfile(path):
            built = False
            path = os.path.join(settings.MEDIA_ROOT, env + '.tgz')
            if not os.path.isfile(path):
                raise Http404("Environment with id '" + env + "' not found")
        else:
            built = True
        
        with open(path, 'rb') as f:
            response = HttpResponse(f.read())
            response['Content-Type'] = "application/gzip"
            response['Content-Disposition'] = ('attachment; filename=' + env
                                               + ("_built.tgz" if built else ".tgz"))
        
        return response



class BuildView(View):
    
    def post(self, request):
        """Build an environment with the content of request."""
        start = time.time()
        logger.info("Build request received from '" + request.META['REMOTE_ADDR'] + "'")
        env_uuid = uuid.uuid4()
        container = None
        path = ""
        
        threading.Thread(target=remove_outdated_env).start()
        
        try:
            while True:
                container = ContainerWrapper.acquire()
                if container is not None:
                    logger.debug("Acquiring a docker took " + str(time.time() - start))
                    break
                
                time.sleep(0.1)
                if time.time() - start > settings.WAIT_FOR_CONTAINER_DURATION:
                    return HttpResponse("Sandbox overloaded", status=503)
            
            test = request.POST.get('test')
            environment = request.FILES.get('environment.tgz')
            if not environment:
                return HttpResponseBadRequest("Missing the parameter 'environment.tgz'")
            
            envname = ("test_" if test is not None else "") + str(env_uuid) + ".tgz"
            path = os.path.join(settings.MEDIA_ROOT, envname)
            with open(path, 'wb') as f:
                f.write(environment.read())
            del environment
            
            logger.debug("POST BUILD took " + str(time.time() - start))
            response = Builder(container, path,
                               request.build_absolute_uri(reverse("sandbox:index"))).execute()
            logger.debug("Total build took " + str(time.time() - start))
        
        except Exception:  # Unknown error
            response = {
                "id"         : str(env_uuid),
                "sandbox_url": request.build_absolute_uri(reverse("sandbox:index")),
                "status"     : SandboxErrCode.UNKNOWN,
                "stderr"     : "",
                "context"    : {},
                "sandboxerr" : "An unknown error occured:\n" + traceback.format_exc()
            }
            logger.exception("An unknown exception occured during build of env %s:" % str(env_uuid))
        
        finally:
            threading.Thread(
                target=get_env_and_reset, args=(container, path, "_built",)
            ).start()
        
        return HttpResponse(json.dumps(response), status=200)



class EvalView(View):
    
    def post(self, request, env):
        """Evaluate an answer inside env."""
        start = time.time()
        logger.info("Evaluate post request received from '" + request.META['REMOTE_ADDR'] + "'")
        container = None
        
        threading.Thread(target=remove_outdated_env).start()
        
        try:
            while True:
                container = ContainerWrapper.acquire()
                if container is not None:
                    logger.debug("Acquiring a docker took " + str(time.time() - start))
                    break
                
                time.sleep(0.1)
                if time.time() - start > settings.WAIT_FOR_CONTAINER_DURATION:
                    logger.warning("Failed to acquire a docker after " + str(time.time() - start))
                    return HttpResponse("Sandbox overloaded", status=503)
            
            answers = request.POST.get('answers')
            if not answers:
                return HttpResponseBadRequest("Missing parameter 'answers'")
            answers = json.loads(answers)
            
            path = os.path.join(settings.MEDIA_ROOT, env + '_built.tgz')
            if not os.path.isfile(path):
                if os.path.isfile(os.path.join(settings.MEDIA_ROOT, env + ".tgz")):
                    # If the unbuilt environment exists, the built one is probably being saved by
                    # another thread, 0.5 sec should be enough for it to finish if that's the case.
                    time.sleep(0.5)
                    if not os.path.isfile(path):
                        raise Http404("Environment with id '" + env + "' not found")
                else:
                    raise Http404("Environment with id '" + env + "' not found")
            
            path = os.path.join(settings.MEDIA_ROOT, env) + "_built.tgz"
            url = request.build_absolute_uri(reverse("sandbox:index"))
            logger.debug("POST EVAL TOOK " + str(time.time() - start))
            response = Evaluator(container, path, url, answers).execute()
            logger.debug("Total eval took " + str(time.time() - start))
        except Exception:  # Unknown error
            response = {
                "id"         : env,
                "sandbox_url": request.build_absolute_uri(reverse("sandbox:index")),
                "status"     : SandboxErrCode.UNKNOWN,
                "grade"      : -1,
                "stderr"     : "",
                "feedback"   : ("Execution of the evaluating script failed due to an unkwown error."
                                + " Please contact your teacher."),
                "context"    : {},
                "sandboxerr" : "An unknown error occured:\n" + traceback.format_exc()
            }
            logger.exception("An unknown exception occured during eval of env %s:" % env)
        finally:
            if container is not None:
                threading.Thread(target=container.release).start()
        
        return HttpResponse(json.dumps(response), status=200)
