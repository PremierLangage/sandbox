
from typing import FrozenSet
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import mixins, viewsets, status

from .serializers import FrozenSerializer
from .models import FrozenResource
from .enums import LoaderErrCode

from hashlib import sha1

import json
class FrozenViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.RetrieveModelMixin,):

    serializer_class = FrozenSerializer
    lookup_field = 'hash'
    lookup_url_kwarg = lookup_field

    @classmethod
    def as_list(cls):
        return cls.as_view({'get': 'list', 'post': 'create'})

    @classmethod
    def as_detail(cls):
        return cls.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'})

    def get_queryset(self):
        return FrozenResource.objects.all()

    def post_frozen(self, request, *args, **kwargs):
        if "data" in request.POST:
            data = {}
            for value in request.POST.getlist("data"):
                dic = json.loads(value)
                for k,v in dic.items():
                    data[k] = v
            hash = sha1(str(data).encode()).hexdigest() # determine hash
            if FrozenResource.objects.filter(hash=hash).count() != 0:
                return Response({"status":LoaderErrCode.ALREADY_PRESENT})
            else:
                FrozenResource.objects.create(hash=hash, data=data)
                return Response({"status":status.HTTP_200_OK})
        return Response({"status",LoaderErrCode.DATA_NOT_PRESENT})

        