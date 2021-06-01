from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.views import APIView

from .serializers import FrozenSerializer
from .models import FrozenResource
from .enums import LoaderErrCode
from .utils import data_to_hash

import json
class FrozenViewSet(APIView):

    serializer_class = FrozenSerializer

    def get(self, request, *args, **kwargs):
        try:
            frozen = FrozenResource.objects.get(hash=kwargs["hash"])
            parents = [p.hash for p in list(frozen.parent.all())]
            return Response({"status":status.HTTP_200_OK, "frozen":{"hash":frozen.hash,"data":frozen.data,"parent":parents}})
        except:
            return Response({"status":LoaderErrCode.FROZEN_RESOURCE_NON_EXISTANT})

    def post(self, request, *args, **kwargs):
        stat = status.HTTP_200_OK
        data = request.POST.get("data")
        if data is None:
            return Response({"status",LoaderErrCode.DATA_NOT_PRESENT})
        
        data = json.loads(data)
        hash = data_to_hash(data)

        result = {
            "hash":hash,
        }

        if FrozenResource.objects.filter(hash=hash).count() != 0:
            frozen = FrozenResource.objects.get(hash=hash)
            stat = LoaderErrCode.ALREADY_PRESENT
        else:
            frozen = FrozenResource.objects.create(hash=hash, data=data)

        parent = request.POST.get("parent")
        if parent is not None:
            try:
                parent_frozen = FrozenResource.objects.get(hash=parent)
                frozen.parent.add(parent_frozen)
                frozen.save()
                result["parent"] = parent
            except ObjectDoesNotExist:
                frozen.delete()
                return Response({"status":LoaderErrCode.NON_EXISTANT_PARENT})
        return Response({"status":stat, "result":result})

        