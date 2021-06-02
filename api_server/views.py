from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from .serializers import FrozenSerializer
from .models import FrozenResource
from .enums import LoaderErrCode
from .utils import data_to_hash

import json
class FrozenViewSet(APIView):

    serializer_class = FrozenSerializer

    def get(self, request):
        hash = request.GET.get("hash")
        if hash is None:
            return Response({"status":LoaderErrCode.DATA_NOT_PRESENT})
        try:
            frozen = FrozenResource.objects.get(hash=hash)
            parents = [p.hash for p in list(frozen.parent.all())]
            return Response({"status":status.HTTP_200_OK, "frozen":{"hash":frozen.hash,"data":frozen.data,"parent":parents}})
        except:
            return Response({"status":LoaderErrCode.NON_EXISTANT_FROZEN_RESOURCE})

    def post(self, request):
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
