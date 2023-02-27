import logging
import threading
import time
from django.views.generic import View
from django.http import HttpResponse, JsonResponse
from django_http_exceptions import HTTPExceptions

from sandbox.containers import Sandbox
from sandbox.executor import Command, Executor
from sandbox_api.errors import LoaderContextError, LoaderError, LoaderInstanceError, LoaderSandboxError

from .loader import Loader

logger = logging.getLogger(__name__)

# Create your views here.

class RunnerView(View):

    def post(self, request):
        start = time.time()
        context = request.POST.dict()
        
        sandbox = Sandbox.acquire()
        try:
            loader = Loader(sandbox, context)
            loader.launch()
            logger.debug(f"Parsing config request took : {time.time() - start} seconds")

            executor = loader.executor(sandbox, request)
            response = executor.execute()
            logger.debug(f"Total execute request took : {time.time() - start} seconds")

            return JsonResponse(response)            

        except LoaderError as e:
            return e.response()
        except LoaderContextError as e:
            return e.response()
        except LoaderInstanceError as e:
            return e.response()
        except LoaderSandboxError as e:
            return e.response()
        except HTTPExceptions.SERVICE_UNAVAILABLE:
            return LoaderSandboxError("Loader sandbox acquire failled, retry after a few seconds").response()
        except TypeError as e:
            return LoaderInstanceError('TypeError').response()
        finally:
            pass
            #threading.Thread(target=sandbox.release).start()
