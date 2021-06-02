from rest_framework.response import Response
from rest_framework import status, mixins, viewsets
from rest_framework.views import APIView

from .serializers import FrozenSerializer
from .models import FrozenResource
from .enums import LoaderErrCode
from .utils import data_to_hash, build_env, build_config, tar_from_dic

import json
import requests
import os

SANDBOX = 'http://127.0.0.1:7000'
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

    def get(self, request):
        hash = request.GET.get("hash")
        if hash is None:
            return Response({"status":LoaderErrCode.DATA_NOT_PRESENT})
        try:
            frozen = FrozenResource.objects.get(hash=hash)
            parents = [p.hash for p in list(frozen.parent.all())]
            return Response({"status":status.HTTP_200_OK, "frozen":{"id":frozen.pk, "hash":frozen.hash,"data":frozen.data,"parent":parents}})
        except:
            return Response({"status":LoaderErrCode.NON_EXISTANT_FROZEN_RESOURCE})

    def post(self, request, hash):
        return_status = status.HTTP_200_OK
        data = request.POST.get("data")
        if data is None:
            return Response({"status":LoaderErrCode.DATA_NOT_PRESENT})
        
        try:
            data = json.loads(data)
            hash = data_to_hash(data)
        except:
            return Response({"status":LoaderErrCode.DATA_NOT_VALID})

        result = {
            "hash":hash,
        }

        try:
            frozen = FrozenResource.objects.get(hash=hash)
            return_status = LoaderErrCode.FROZEN_RESOURCE_ALREADY_PRESENT
        except:
            frozen = FrozenResource.objects.create(hash=hash, data=data)

        result["id"] = frozen.pk
        parent = request.POST.get("parent")
        if parent is not None:
            try:
                parent_frozen = FrozenResource.objects.get(hash=parent)
                frozen.parent.add(parent_frozen)
                frozen.save()
                result["parent"] = parent
            except:
                frozen.delete()
                return_status = LoaderErrCode.NON_EXISTANT_PARENT
        return Response({"status":return_status, "result":result})

    def play_demo(self, request):
        data = request.POST.get("data")
        answer = None
        if data is None:
            return Response({"status":LoaderErrCode.DATA_NOT_PRESENT})

        if "answer" in data and "env_id" in data:
            answer = data["answer"]
            env_id = data["env_id"]
            env = {'environment':tar_from_dic({answer.json:json.dumps(answer)})}
        else:
            env = {'environment':build_env(json.loads(data))}

        if answer:
            config = build_config(['sh grader.sh'], True, environment=env_id)
        else:
            config = build_config(['sh builder.sh'], True)

        url = os.path.join(SANDBOX, "execute/")
        response = requests.post(url, data=config, files=env)
        return Response({"result":response})
        
