#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Python [3.6]
#
#  Author: Coumes Quentin     Mail: qcoumes@etud.u-pem.fr
#  Created: 2017-07-30
#  Last Modified: 2017-09-30


import os, time, shutil, logging

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, Http404

from sandbox.executor import Executor

logger = logging.getLogger(__name__)


@csrf_exempt
def execute(request):
    if request.META["REQUEST_METHOD"] == "HEAD":
        logger.info("HEAD request received from '"+request.META['REMOTE_ADDR']+"'");
        return HttpResponse('OK !', status=200)
    if request.META["REQUEST_METHOD"] != "POST":
        logger.warning("Invalid methode ("+request.META["REQUEST_METHOD"]+") received from '"+request.META['REMOTE_ADDR']+"'");
        return HttpResponse('405 Method Not Allowed', status=405)
    
    # Removing tmp files older than 2 hours
    current_time = time.time()
    for f in os.listdir(settings.MEDIA_ROOT):
        if "README" in f:
            continue
        creation_time = os.path.getctime(settings.MEDIA_ROOT+"/"+f)
        if (current_time - creation_time) >= 7200:
            shutil.rmtree(settings.MEDIA_ROOT+"/"+f)
            
    logger.info("Sandbox request received from '"+request.META['REMOTE_ADDR']+"'");
    try:
        return HttpResponse(Executor(request).execute())
    except: 
        logger.exception("Unknown Error:")
        return HttpResponse('520 Unknown Error', status=520)

@csrf_exempt
def action(request):
    if "action" in request.GET:
        l = request.GET["action"]
    elif "action" in request.POST:
        l = request.POST["action"]
    else:
        return Http404("Aucune action définie.")
    if l == "languages":
        return HttpResponse('{"languages":["c","python"]}')
    if l == "version":
        return HttpResponse('{"version":"pysandbox-0.1"}')
    if l != "execute":
        return Http404("Erreur - Action inconnue: "+ l)
    
    return execute(request)
