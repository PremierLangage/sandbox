import json
import io
from django.test.utils import captured_output

from rest_framework.response import Response
from rest_framework import status, mixins, viewsets

from .serializers import FrozenSerializer
from .models import FrozenResource
from .enums import LoaderErrCode
from .utils import data_to_hash, build_env, build_config, tar_from_dic

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

    def get(self, request, id):
        try:
            frozen = FrozenResource.objects.get(id=id)
            parents = [p.id for p in list(frozen.parent.all())]
            return Response({"status":status.HTTP_200_OK, "frozen":{"id":frozen.pk, "hash":frozen.hash,"data":frozen.data,"parent":parents}})
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

        try:
            frozen = FrozenResource.objects.get(hash=hash)
            return_status = LoaderErrCode.FROZEN_RESOURCE_ALREADY_PRESENT
        except:
            frozen = FrozenResource.objects.create(hash=hash, data=data)

        result = {
            "hash":hash,
            "id":frozen.pk,
        }
        parent = request.POST.get("parent")
        if parent is not None:
            try:
                parent_frozen = FrozenResource.objects.get(id=parent)
                frozen.parent.add(parent_frozen)
                frozen.save()
                result["parent"] = parent
            except:
                frozen.delete()
                del result["id"]
                return_status = LoaderErrCode.NON_EXISTANT_PARENT
        return Response({"status":return_status, "result":result})

    
        
class CallSandboxViewSet(
    viewsets.GenericViewSet
):
    def play_demo(self, request):
        data = request.POST.get("data")

        if data is None:
            return Response({"status":LoaderErrCode.DATA_NOT_PRESENT})
        try:
            data = json.loads(data)
        except:
            return Response({"status":LoaderErrCode.DATA_NOT_VALID})

        if "answer" in data and "env_id" in data:
            answer = data["answer"]
            env_id = data["env_id"]
            env = tar_from_dic({"answers.json":json.dumps(answer)})
            config = build_config(['sh grader.sh'], True, environment=env_id, result_path="feedback.html")
        else:
            env = build_env(data)
            config = build_config(['sh builder.sh'], True)

        request.FILES["environment"] = io.BytesIO(env)

        _mutable = request._request._post._mutable
        request._request._post._mutable = True
        request._request._post["config"] = config
        request._request._post._mutable = _mutable

        return Response(json.loads(ExecuteView.as_view()(request).content))