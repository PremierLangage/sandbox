import json
import os

from django.core.exceptions import ObjectDoesNotExist

from rest_framework.response import Response
from rest_framework import status, mixins, viewsets
from rest_framework.request import Request

from json.decoder import JSONDecodeError

from .serializers import FrozenSerializer
from .models import FrozenResource
from .enums import CallSandboxErrCode, LoaderErrCode
from .utils import build_config, build_env, data_to_hash, build_resource, build_request, tar_from_dic

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
            return Response({"status":status.HTTP_200_OK, "frozen":{"id":frozen.pk, "hash":frozen.hash,"data":frozen.data}})
        except:
            return Response({"status":LoaderErrCode.NON_EXISTANT_FROZEN_RESOURCE})

    def post(self, request: Request):
        """
            Load a Resource to the sandbox. Save it into a FrozenResource.
            Return the id and the hash of the FrozenResource.
        """
        data = request.POST.get("data")
        if data is None:
            return Response({"status":LoaderErrCode.DATA_NOT_PRESENT})
        
        try:
            data = json.loads(data)
            hash = data_to_hash(data)
        except JSONDecodeError:
            return Response({"status":LoaderErrCode.DATA_NOT_VALID})

        frozen, created = FrozenResource.objects.get_or_create(hash=hash, data=data)

        result = {
            "id":frozen.pk,
            "hash":hash,
        }

        if not created:
            return Response({"status":LoaderErrCode.FROZEN_RESOURCE_ALREADY_PRESENT, "result":result})
        
        return Response({"status":status.HTTP_200_OK, "result":result})


class CallSandboxViewSet(viewsets.GenericViewSet):
    def play_demo(self, request: Request):
        data = request.data.get("data")

        if data is None:
            return Response({"status":LoaderErrCode.DATA_NOT_PRESENT})
        try:
            data = json.loads(data)
        except JSONDecodeError:
            return Response({"status":LoaderErrCode.DATA_NOT_VALID})
        
        path = request.data.get("path")
        
        env, config = build_resource(request, data, path)

        build_request(request, env=env, post={"config":config, "path":path})

        return Response(json.loads(ExecuteView.as_view()(request).content))
    
    def _build_act(self, frozen_id):
        try:
            frozen = FrozenResource.objects.get(id=int(frozen_id))
            data_activity = frozen.data
            data_activity["name_exos"] = dict()
        except ObjectDoesNotExist as odne:
            raise odne
            
        files = dict()
        if "__files" in data_activity:
            for f in data_activity["__files"]:
                files[f] = data_activity["__files"][f]
        for pl in data_activity["lst_exos"]:
            try:
                frozen = FrozenResource.objects.get(id=int(pl))
                pl_data = frozen.data
            except ObjectDoesNotExist as odne:
                raise odne
            files[str(pl)+".json"] = json.dumps(pl_data)
            files.update(build_env(pl_data, path=os.path.join(str(pl),"")))
            data_activity["name_exos"][str(pl)] = pl_data["title"]
        
        data_activity["current"] = 0
        files["activity.json"] = json.dumps(data_activity)
        return files
    
    def execute(self, request: Request):
        path_command = request.data.get("path_command")
        command = request.data.getlist("command")
        frozen_id = request.data.get("frozen_resource_id")
        answer = request.data.get("answer")
        env_id = request.data.get("env_id")
        path_env = request.data.get("path_env")
        result = request.data.get("result")

        if path_command is None:
            return Response({"status":CallSandboxErrCode.PATH_COMMAND_NOT_PRESENT, "stderr":"path_command is not present"})

        if len(command) == 0:
            return Response({"status":CallSandboxErrCode.COMMAND_NOT_PRESENT, "stderr":"command is not present"})

        files = dict()

        if frozen_id is not None:
            try:
                pl_files = self._build_act(frozen_id)
                files.update(pl_files)
            except ObjectDoesNotExist:
                return Response({
                    "status":CallSandboxErrCode.INVALID_FROZEN_RESOURCE_ID,
                    "stderr":f"The id : {frozen_id} do not correspond to a FrozenResource"
                })
        
        if answer is not None:
            files.update({f"{path_command}/answers.json":answer})

        commands = [' && '.join([f'cd {path_command}'] + command)]
        config = build_config(list_commands=commands, save=True, environment=env_id, result_path=result)
        env = tar_from_dic(files=files)

        build_request(request=request, post={"config":config, "path":path_env}, env=env)
        
        return Response(json.loads(ExecuteView.as_view()(request).content))
