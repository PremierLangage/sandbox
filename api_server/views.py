import json
import io

from rest_framework.response import Response
from rest_framework import status, mixins, viewsets
from rest_framework.request import Request

from .serializers import FrozenSerializer
from .models import FrozenResource
from .enums import LoaderErrCode
from .utils import build_resource, build_resource_demo, data_to_hash

from sandbox.views import ExecuteView


class FrozenViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.RetrieveModelMixin,
):

    serializer_class = FrozenSerializer

    lookup_field = 'id'
    lookup_url_kwarg = lookup_field

    def get_queryset(self):
        return FrozenResource.objects.all()

    def get(self, request, id: int):
        """
            Return a specified FrozenResource

            :param id:  The id of FrozenResource to return
        """
        try:
            frozen = FrozenResource.objects.get(id=id)
            parents = [p.id for p in list(frozen.parent.all())]
            return Response({"status":status.HTTP_200_OK, "frozen":{"id":frozen.pk, "hash":frozen.hash,"data":frozen.data,"parent":parents}})
        except:
            return Response({"status":LoaderErrCode.NON_EXISTANT_FROZEN_RESOURCE})

    def post(self, request: Request):
        """
            Load a Resource to the sandbox. Save it into a FrozenResource.
            Return the id and the hash of the FrozenResource.
        """
        return_status = status.HTTP_200_OK
        data = request.POST.get("data")
        if data is None:
            return Response({"status":LoaderErrCode.DATA_NOT_PRESENT})
        
        try:
            data = json.loads(data)
            hash = data_to_hash(data)
        except:
            return Response({"status":LoaderErrCode.DATA_NOT_VALID})

        try:
            frozen = FrozenResource.objects.get(hash=hash)
            return_status = LoaderErrCode.FROZEN_RESOURCE_ALREADY_PRESENT
        except:
            frozen = FrozenResource.objects.create(hash=hash, data=data)

        result = {
            "id":frozen.pk,
            "hash":hash,
        }
        parent = request.POST.get("parent")
        if parent is not None:
            try:
                parent_frozen = FrozenResource.objects.get(id=parent)
                frozen.parent.add(parent_frozen)
                frozen.save()
            except:
                frozen.delete()
                return Response({"status":LoaderErrCode.NON_EXISTANT_PARENT})
        return Response({"status":return_status, "result":result})

    
class CallSandboxViewSet(viewsets.GenericViewSet):
    def _build_request(self, request: Request, env: str, config: dict):
        request._request.FILES["environment"] = io.BytesIO(env)

        _mutable = request._request.POST._mutable
        request._request.POST._mutable = True
        request._request.POST["config"] = config
        request._request.POST._mutable = _mutable

    def play_demo(self, request: Request):
        data = request.POST.get("data")

        if data is None:
            return Response({"status":LoaderErrCode.DATA_NOT_PRESENT})
        try:
            data = json.loads(data)
        except:
            return Response({"status":LoaderErrCode.DATA_NOT_VALID})

        env, config = build_resource_demo(data=data)

        self._build_request(request, env=env, config=config)

        return Response(json.loads(ExecuteView.as_view()(request).content))
    
    def play_exo(self, request: Request):
        data = request.POST.get("data")
        if data is None:
            return Response({"status":LoaderErrCode.DATA_NOT_PRESENT})
        try:
            data = json.loads(data)
        except:
            return Response({"status":LoaderErrCode.DATA_NOT_VALID})

        env, config = build_resource(data=data)

        if env == None:
            return Response({"status":LoaderErrCode.FROZEN_RESOURCE_ID_NOT_PRESENT})

        self._build_request(request, env=env, config=config)

        return Response(json.loads(ExecuteView.as_view()(request).content))
    
        
        
        




        