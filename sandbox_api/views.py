import threading
import time
import json
import logging
from django.shortcuts import render
from django.views.generic import View
from django.http import (HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed,
                         HttpResponseNotFound, JsonResponse)

from sandbox import utils
import sandbox
from sandbox.containers import Sandbox
from sandbox.executor import Command, Executor
from sandbox_api.errors import LoaderInstanceError
from .utils import load_files, load_includes

from .loader import Loader

logger = logging.getLogger(__name__)

# Create your views here.

class RunnerView(View):

    def post(self, request):
        config = request.POST.get("config")
        loader = request.POST.get("loader")

        sandbox = Sandbox.acquire()
        try: 
            loader = Loader(sandbox, request.POST.get("loader"), request.POST.get("config"))
        except LoaderInstanceError as error:
            return JsonResponse(error)
        
