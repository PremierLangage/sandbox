from rest_framework.response import Response
from rest_framework import mixins, viewsets, status
from django.core.exceptions import ObjectDoesNotExist

from .serializers import FrozenSerializer
from .models import FrozenResource
from .enums import LoaderErrCode
from .utils import data_to_hash

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
                return Response({"status":LoaderErrCode.UNEXISTANT_PARENT})
        return Response({"status":stat, "result":result})

        