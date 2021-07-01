import json
import os

from rest_framework.response import Response
from rest_framework import status, mixins, viewsets
from rest_framework.request import Request

from json.decoder import JSONDecodeError

from .serializers import FrozenSerializer
from .models import FrozenResource
from .enums import CallSandboxErrCode, LoaderErrCode
from .utils import build_config, build_env_act, data_to_hash, build_resource, build_request, tar_from_dic

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
    def _play(self, request: Request, is_demo: bool):
        data = request.data.get("data")

        if data is None:
            return Response({"status":LoaderErrCode.DATA_NOT_PRESENT})
        try:
            data = json.loads(data)
        except JSONDecodeError:
            return Response({"status":LoaderErrCode.DATA_NOT_VALID})
        
        path = request.data.get("path")
        
        ret = build_resource(request, data, is_demo, path)

        if isinstance(ret, LoaderErrCode):
            return Response({"status":ret})

        env, config = ret

        build_request(request, env=env, post={"config":config, "path":path})

        return Response(json.loads(ExecuteView.as_view()(request).content))

    def play_demo(self, request: Request):
        return self._play(request, is_demo=True)
    
    def play_exo(self, request: Request):
        return self._play(request, is_demo=False)
    
    def _build_act(self, frozen_id):
        try:
            frozen = FrozenResource.objects.get(id=int(frozen_id))
            data = frozen.data
        except:
            return Response({
                "status":LoaderErrCode.FROZEN_RESOURCE_ID_NOT_IN_DB,
                "stderr":f"The id : {frozen_id} do not correspond to a FrozenResource"
            })
        files = dict()
        data_activity = frozen.data
        if "__files" in data_activity:
            for f in data_activity["__files"]:
                files[f] = data_activity["__files"][f]
        files["output.json"] = ""
        files["result.json"] = ""
        for pl in data_activity["lst_exos"]:
            try:
                frozen = FrozenResource.objects.get(id=int(pl))
                pl_data = frozen.data
            except:
                return Response({"status":LoaderErrCode.FROZEN_RESOURCE_ID_NOT_IN_DB})
            files[str(pl)+".json"] = pl_data
            files.update(build_env_act(pl_data, path=str(pl)+"/"))
        
        data_activity["current"] = 0
        files["activity.json"] = json.dumps(data_activity)
        return files
    
    def execute(self, request: Request):
        path_command = request.data.get("path_command")
        command = request.data.getlist("command")
        frozen_id = request.data.get("frozen_resource_id")
        result = request.data.get("result")
        env_id = request.data.get("env_id")
        path_env = request.data.get("path_env")

        if path_command is None:
            return Response({"status":CallSandboxErrCode.PATH_COMMAND_NOT_PRESENT, "stderr":"path_command is not present"})

        if command is None:
            return Response({"status":CallSandboxErrCode.COMMAND_NOT_PRESENT, "stderr":"command is not present"})

        files = dict()

        if frozen_id is not None:
            files.update(self._build_act(frozen_id))

        if result is not None:
            files.update({"answer":json.dumps(result)})

        commands = [f'cd {path_command}']
        for i in range(len(command)):
            files[str(i) + ".sh"] = command[i]
            commands.append(f'sh {str(i)}.sh')

        config = build_config(list_commands=commands, save=True, environment=env_id)
        env = tar_from_dic(files=files)

        build_request(request=request, post={"config":config, "path":path_env}, env=env)
        
        response = json.loads(ExecuteView.as_view()(request).content)

        return Response(response)
        
