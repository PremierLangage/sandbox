#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Python [3.6]
#
#  Author: Coumes Quentin     Mail: qcoumes@etud.u-pem.fr
#  Created: 2017-07-30
#  Last Modified: 2017-09-30


import os, time, shutil, logging, uuid, json, traceback
from distutils.version import StrictVersion

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, Http404, HttpResponseBadRequest
from django.views.generic import View
from django.urls import reverse

from sandbox.executor import Builder, Evaluator
from sandbox.utils import remove_outdated_env
from sandbox.enums import SandboxErrCode

logger = logging.getLogger(__name__)


class IndexView(View):
    """Check wether the sandbox can execute a request according to the version."""
    
    def head(self, request):
        logger.info("Head request received from '" + request.META['REMOTE_ADDR'] + "'")
        
        if 'version' not in request.GET:
            return HttpResponseBadRequest("Missing parameter 'version'")
        
        try:
            version = request.GET.get('version')
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
    """Return the version of the sandbox."""
    
    def get(self, request):
        logger.info("Version request received from '" + request.META['REMOTE_ADDR'] + "'")
        return HttpResponse('{"version": ' + settings.SANDBOX_VERSION + '}', status=200)



class EnvView(View):
    """Allow to download an environment for testings purpose."""
    
    def head(self, request, env):
        logger.info("Env head request received from '" + request.META['REMOTE_ADDR'] + "' with ID '" + env + "'")
        remove_outdated_env()
        
        path = os.path.join(settings.MEDIA_ROOT, env + '_built.tgz')
        if not os.path.isfile(path):
            path = os.path.join(settings.MEDIA_ROOT, env + '.tgz')
            if not os.path.isfile(path):
                raise Http404("Environment with id '" + env + "' not found")
        
        return HttpResponse(status=204)
    
    
    def get(self, request, env):
        logger.info("Env get request received from '" + request.META['REMOTE_ADDR'] + "' with ID '" + env + "'")
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
        try:
            logger.info("Build request received from '" + request.META['REMOTE_ADDR'] + "'")
            env_uuid = uuid.uuid4()
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
        try:
            logger.info("Evaluate post request received from '" + request.META['REMOTE_ADDR'] + "'")
            remove_outdated_env()
            
            answers = request.POST.get('answers')
            if not answers:
                return HttpResponseBadRequest("Missing parameter 'answers'")
            
            path = os.path.join(settings.MEDIA_ROOT, env + '_built.tgz')
            if not os.path.isfile(path):
                raise Http404("Environment with id '" + env + "' not found")
            
            response = Evaluator(path, request.build_absolute_uri(reverse("sandbox:index")), answers).execute()
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
