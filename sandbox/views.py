#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Python [3.6]
#
#  Author: Coumes Quentin     Mail: qcoumes@etud.u-pem.fr
#  Created: 2017-07-30
#  Last Modified: 2017-09-30


import os, time, logging, uuid, json, traceback
from distutils.version import StrictVersion

from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponseBadRequest
from django.views.generic import View
from django.urls import reverse

from sandbox.executor import Builder, Evaluator
from sandbox.utils import remove_outdated_env
from sandbox.enums import SandboxErrCode

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
    
    def head(self, request, env):
        """Return status 204 if env was found, 404 if not."""
        logger.info("Env head request received from '" + request.META['REMOTE_ADDR']
                    + "' with ID '" + env + "'")
        remove_outdated_env()
        
        path = os.path.join(settings.MEDIA_ROOT, env + '_built.tgz')
        if not os.path.isfile(path):
            path = os.path.join(settings.MEDIA_ROOT, env + '.tgz')
            if not os.path.isfile(path):
                raise Http404("Environment with id '" + env + "' not found")
        
        return HttpResponse(status=204)
    
    
    def get(self, request, env):
        """Return the environment, status 404 if the environment could not be found."""
        logger.info("Env get request received from '" + request.META['REMOTE_ADDR']
                    + "' with ID '" + env + "'")
        remove_outdated_env()
        
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
        """Build an environment with the content of request. See swagger for more informations"""
        logger.info("Build request received from '" + request.META['REMOTE_ADDR'] + "'")
        env_uuid = uuid.uuid4()
        try:
            remove_outdated_env()
            
            test = request.POST.get('test')
            environment = request.FILES.get('environment.tgz')
            
            if not environment:
                return HttpResponseBadRequest("Missing  at least one of the parameters " 
                                              + "'test' or 'environment.tgz'")
            
            envname = ("test_" if test is not None else "") + str(env_uuid) + ".tgz"
            path = os.path.join(settings.MEDIA_ROOT, envname)
            
            with open(os.path.join(path), 'wb') as f:
                f.write(environment.read())
            del environment
            
            response = Builder(path, request.build_absolute_uri(reverse("sandbox:index"))).execute()
        except Exception:  # Unknown error
            response = {
                "id": str(env_uuid),
                "sandbox_url": request.build_absolute_uri(reverse("sandbox:index")),
                "status": SandboxErrCode.UNKNOWN,
                "stderr": "",
                "context": {},
                "sandboxerr": "An unknown error occured:\n" + traceback.format_exc()
            }
            logger.exception("An unknown exception occured during build of env %s:" % str(env_uuid))
        return HttpResponse(json.dumps(response), status=200)



class EvalView(View):
    
    def post(self, request, env):
        """Evaluate an answer inside env. See swagger for more information."""
        try:
            logger.info("Evaluate post request received from '" + request.META['REMOTE_ADDR'] + "'")
            remove_outdated_env()
            
            answers = request.POST.get('answers')
            if not answers:
                return HttpResponseBadRequest("Missing parameter 'answers'")
            
            path = os.path.join(settings.MEDIA_ROOT, env + '_built.tgz')
            if not os.path.isfile(path):
                if os.path.isfile(os.path.join(settings.MEDIA_ROOT, env + ".tgz")):
                    # If the unbuilt environment exists, the built one is probably being saved by
                    # another thread, 1 sec should be enough for it to finish if that's the case.
                    time.sleep(1)
                    if not os.path.isfile(path):
                        raise Http404("Environment with id '" + env + "' not found")
                else:
                    raise Http404("Environment with id '" + env + "' not found")

            url = request.build_absolute_uri(reverse("sandbox:index"))
            response = Evaluator(path, url, answers).execute()
        except Exception:  # Unknown error
            response = {
                "id": env,
                "sandbox_url": request.build_absolute_uri(reverse("sandbox:index")),
                "status": SandboxErrCode.UNKNOWN,
                "grade": -1,
                "stderr": "",
                "feedback": ("Execution of the evaluating script failed due to an unkwown error."
                             + " Please contact your teacher."),
                "context": {},
                "sandboxerr": "An unknown error occured:\n" + traceback.format_exc()
            }
            logger.exception("An unknown exception occured during eval of env %s:" % env)
        return HttpResponse(json.dumps(response), status=200)
