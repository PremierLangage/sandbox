import json

from rest_framework.response import Response
from rest_framework import status, mixins, viewsets
from rest_framework.request import Request

from json.decoder import JSONDecodeError

from .serializers import FrozenSerializer
from .models import FrozenResource
from .enums import LoaderErrCode
from .utils import data_to_hash, build_resource, build_request

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
        except JSONDecodeError:
            return Response({"status":LoaderErrCode.DATA_NOT_VALID})

        frozen, created = FrozenResource.objects.get_or_create(hash=hash, data=data)
        if not created:
            return_status = LoaderErrCode.FROZEN_RESOURCE_ALREADY_PRESENT

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
    def _play(self, request: Request, is_demo: bool):
        data = request.POST.get("data")

        if data is None:
            return Response({"status":LoaderErrCode.DATA_NOT_PRESENT})
        try:
            data = json.loads(data)
        except:
            return Response({"status":LoaderErrCode.DATA_NOT_VALID})

        env, config = build_resource(data, is_demo)

        if config == None:
            return Response({"status":env})

        build_request(request, env=env, config=config)

        return Response(json.loads(ExecuteView.as_view()(request).content))

    def play_demo(self, request: Request):
        return self._play(request, is_demo=True)
    
    def play_exo(self, request: Request):
        return self._play(request, is_demo=False)
    
        
        
        




        