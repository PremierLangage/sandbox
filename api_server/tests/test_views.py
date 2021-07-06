import json
import os

import settings

from random import randint
from typing import List

from django.test.utils import override_settings
from sandbox.tasks import remove_expired_env

from django.test import TestCase
from django.urls import reverse

from api_server.utils import data_to_hash
from api_server.enums import CallSandboxErrCode, LoaderErrCode
from api_server.models import FrozenResource

from sandbox.containers import initialise_containers, purging_containers

from settings import ENVIRONMENT_ROOT, ENVIRONMENT_EXPIRATION


TEST_DATA_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_data")

MAX_PATHS = 20
NB_COURSE = 2
NB_ACTIVITIES = 2
NB_USERS = 2
NB_EXERCICES = 2

class FrozenTestCase(TestCase):

    def setUp(self) -> None:
        self.data1 = {"data":"frozen1"}
        self.data2 = {"data":"frozen2"}
        self.data3 = {"data":"frozen3"}

        self.frozen1 = FrozenResource.objects.create(hash=data_to_hash(self.data1), data=self.data1)
        self.frozen2 = FrozenResource.objects.create(hash=data_to_hash(self.data2), data=self.data2)

        with open(os.path.join(TEST_DATA_ROOT, "basic_pl1.json")) as f:
            self.pl_data1 = json.load(f)

        super().setUp()
    
    
    def test_get(self):
        response = self.client.get(reverse('api_server:frozen_get', args=[self.frozen1.id]))
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], 200)

        frozen = response["frozen"]
        self.assertEqual(frozen["hash"], data_to_hash(self.data1))
        self.assertEqual(frozen["data"], self.data1)

    def test_get_non_existant(self):
        response = self.client.get(reverse('api_server:frozen_get', args=[10]))
        response = json.loads(response.content.decode())
        self.assertEqual(response["status"], LoaderErrCode.NON_EXISTANT_FROZEN_RESOURCE)
    
    def test_post(self):
        data = {"data":json.dumps(self.data3)}
        response = self.client.post(reverse("api_server:frozen_post"), data=data)
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], 200)
        self.assertEqual(response["result"]["hash"], data_to_hash(self.data3))

        response = self.client.get(reverse("api_server:frozen_get", args=[response["result"]["id"]]))
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], 200)

        frozen = response["frozen"]
        self.assertEqual(frozen["hash"], data_to_hash(self.data3))
        self.assertEqual(frozen["data"], self.data3)

    def test_post_already_present(self):
        data = {"data":json.dumps(self.data1)}
        response = self.client.post(reverse("api_server:frozen_post"), data=data)
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], LoaderErrCode.FROZEN_RESOURCE_ALREADY_PRESENT)
        self.assertEqual(response["result"]["hash"], data_to_hash(self.data1))

    def test_post_without_data(self):
        response = self.client.post(reverse("api_server:frozen_post"))
        response = json.loads(response.content.decode())
        self.assertEqual(response["status"], LoaderErrCode.DATA_NOT_PRESENT)

    def test_post_data_not_valid(self):
        response = self.client.post(reverse("api_server:frozen_post"), data={"data":"data"})
        response = json.loads(response.content.decode())
        self.assertEqual(response["status"], LoaderErrCode.DATA_NOT_VALID)


class CallSandboxTestCase(TestCase):
    def setUp(self) -> None:
        with open(os.path.join(TEST_DATA_ROOT, "basic_pl1.json")) as f:
            self.pl_data1 = json.load(f)

        with open(os.path.join(TEST_DATA_ROOT, "basic_pl2.json")) as f:
            self.pl_data2 = json.load(f)

        with open(os.path.join(TEST_DATA_ROOT, "basic_activity.json")) as f:
            self.activity_data = json.load(f)

        courses = ["course" + str(i+1) for i in range(NB_COURSE)]
        activities = ["activity" + str(i+1) for i in range(NB_ACTIVITIES)]
        users = ["user" + str(i+1) for i in range(NB_USERS)]
        exercices = ["exercice" + str(i+1) for i in range(NB_EXERCICES)]

        self.paths = list()
        
        for i in range(MAX_PATHS):
            course = courses[randint(0, len(courses)-1)]
            activity = activities[randint(0, len(activities)-1)]
            user = users[randint(0, len(users)-1)]
            exercice = exercices[randint(0, len(exercices)-1)]

            self.paths.append(os.path.join(course, activity, user, exercice))

        purging_containers()
        initialise_containers()

        super().setUp()

    def tearDown(self) -> None:
        remove_expired_env()
        purging_containers()
        super().tearDown()

    def push_frozen(self, push):
        data = {"data": json.dumps(push)}

        response = self.client.post(reverse("api_server:frozen_post"), data=data)
        response = json.loads(response.content.decode())
        return response["result"]["id"]

@override_settings(ENVIRONMENT_EXPIRATION=1)
class PlayDemoTestCase(CallSandboxTestCase):
    def setUp(self) -> None:
        super().setUp()

    
    def tearDown(self) -> None:
        super().tearDown()

    def test_play_demo_good_answer(self):
        data = {"data": json.dumps(self.pl_data1)}
        
        response = self.client.post(reverse("api_server:play_demo"), data=data)
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], 0)

        data = data={"data":json.dumps({"answer":{"answer": "pim = 1\npam = 2\npom = 3"}, "env_id":response["environment"]})}
        response = self.client.post(reverse("api_server:play_demo"), data=data)
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], 0)
        self.assertEqual(response["execution"][0]["stdout"], "100")

    def test_play_demo_wrong_answer(self):
        data = {"data": json.dumps(self.pl_data1)}
        
        response = self.client.post(reverse("api_server:play_demo"), data=data)
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], 0)

        data = {"data":json.dumps({"answer":{"answer": ""}, "env_id":response["environment"]})}
        response = self.client.post(reverse("api_server:play_demo"), data=data)
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], 0)
        self.assertEqual(response["execution"][0]["stdout"], "0")

    def test_play_demo_with_path(self):
        data = {"data": json.dumps(self.pl_data1), "path": self.paths[0]}
        
        response = self.client.post(reverse("api_server:play_demo"), data=data)
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], 0)

        data = {"data":json.dumps({"answer":{"answer": "pim = 1\npam = 2\npom = 3"}, "env_id":response["environment"]}), "path": self.paths[0]}
        response = self.client.post(reverse("api_server:play_demo"), data=data)
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], 0)
        self.assertEqual(response["execution"][0]["stdout"], "100")

    def test_play_demo_with_many_path(self):
        for path in self.paths:
            data = {"data": json.dumps(self.pl_data1), "path": path}
            
            response = self.client.post(reverse("api_server:play_demo"), data=data)
            response = json.loads(response.content.decode())

            self.assertEqual(response["status"], 0)

            data = {"data":json.dumps({"answer":{"answer": "pim = 1\npam = 2\npom = 3"}, "env_id":response["environment"]}), "path": path}
            response = self.client.post(reverse("api_server:play_demo"), data=data)
            response = json.loads(response.content.decode())

            self.assertEqual(response["status"], 0)
            self.assertEqual(response["execution"][0]["stdout"], "100")
    
    def test_play_demo_data_not_present(self):
        data = {"wrong": json.dumps(self.pl_data1)}
        
        response = self.client.post(reverse("api_server:play_demo"), data=data)
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], LoaderErrCode.DATA_NOT_PRESENT)

    def test_play_demo_data_not_valid(self):
        data = {"data": self.pl_data1}
        
        response = self.client.post(reverse("api_server:play_demo"), data=data)
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], LoaderErrCode.DATA_NOT_VALID)

@override_settings(ENVIRONMENT_EXPIRATION=1)
class PlayActivityTestCase(CallSandboxTestCase):
    def setUp(self) -> None:
        super().setUp()

    
    def tearDown(self) -> None:
        super().tearDown()

    def push_frozen_activity(self, activity: dict, exercices: List[dict]):
        pls = []
        for i in exercices:
            pl_id = self.push_frozen(i)
            pls.append(pl_id)
        activity["lst_exos"] = pls
        return self.push_frozen(activity)

    def _start_activity(self, data):
        response = self.client.post(
            reverse("api_server:execute"),
            data=data
        )
        return json.loads(response.content.decode())

    def test_start_activity(self):
        id = self.push_frozen_activity(self.activity_data, [self.pl_data1])

        data={
            "path_command":".",
            "command":["python3 start.py activity.json output.json result.json"],
            "frozen_resource_id":id,
        }
        response = self.client.post(
            reverse("api_server:execute"),
            data=data
        )
        response = json.loads(response.content.decode())
        
        self.assertEqual(response["status"], 0)
        self.assertEqual(int(response["execution"][0]["stdout"]), self.activity_data["lst_exos"][0])
        self.assertTrue(os.path.exists(os.path.join(settings.ENVIRONMENT_ROOT, response["environment"])+".tgz"))

    def test_start_activity_without_path_command(self):
        id = self.push_frozen_activity(self.activity_data, [self.pl_data1])

        data={
            "command":["python3 start.py activity.json output.json result.json"],
            "frozen_resource_id":id,
        }
        response = self.client.post(
            reverse("api_server:execute"),
            data=data
        )
        response = json.loads(response.content.decode())
        
        self.assertEqual(response["status"], CallSandboxErrCode.PATH_COMMAND_NOT_PRESENT)
        self.assertEqual(response["stderr"], "path_command is not present")

    def test_start_activity_without_command(self):
        id = self.push_frozen_activity(self.activity_data, [self.pl_data1])

        data={
            "path_command":".",
            "frozen_resource_id":id,
        }
        response = self.client.post(
            reverse("api_server:execute"),
            data=data
        )
        response = json.loads(response.content.decode())
        
        self.assertEqual(response["status"], CallSandboxErrCode.COMMAND_NOT_PRESENT)
        self.assertEqual(response["stderr"], "command is not present")

    def test_start_activity_invalid_activity_id(self):
        """
            Wrong id to activity frozen resource
        """
        id = self.push_frozen_activity(self.activity_data, [self.pl_data1])

        data={
            "path_command":".",
            "command":["python3 start.py activity.json output.json result.json"],
            "frozen_resource_id":id+1,
        }
        response = self.client.post(
            reverse("api_server:execute"),
            data=data
        )
        response = json.loads(response.content.decode())
        
        self.assertEqual(response["status"], CallSandboxErrCode.INVALID_FROZEN_RESOURCE_ID)
        self.assertEqual(response["stderr"], f"The id : {id+1} do not correspond to a FrozenResource")


        """
            Wrong id to exercice frozen resource
        """
        self.activity_data["lst_exos"] = [-1]
        id =  self.push_frozen(self.activity_data)

        data={
            "path_command":".",
            "command":["python3 start.py activity.json output.json result.json"],
            "frozen_resource_id":id,
        }
        response = self.client.post(
            reverse("api_server:execute"),
            data=data
        )
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], CallSandboxErrCode.INVALID_FROZEN_RESOURCE_ID)
        self.assertEqual(response["stderr"], f"The id : {id} do not correspond to a FrozenResource")

    def test_start_activity_invalid_exercice_id(self):
        id =  self.push_frozen(self.activity_data)

        data={
            "path_command":".",
            "command":["python3 start.py activity.json output.json result.json"],
            "frozen_resource_id":id,
        }
        response = self.client.post(
            reverse("api_server:execute"),
            data=data
        )
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], CallSandboxErrCode.INVALID_FROZEN_RESOURCE_ID)
        self.assertEqual(response["stderr"], f"The id : {id} do not correspond to a FrozenResource")

    def test_response_good_answer(self):
        id = self.push_frozen_activity(self.activity_data, [self.pl_data1])
        response = self._start_activity(data={
            "path_command":".",
            "command":["python3 start.py activity.json output.json result.json"],
            "frozen_resource_id":id,
        })

        repo = response['execution'][0]['stdout']
        env = response['environment']

        data={
            "path_command":repo,
            "command":["python3 grader.py pl.json answers.json processed.json feedback.html 2> stderr.log"],
            "env_id":env,
            "answer":json.dumps({"answer": "pim = 1\npam = 2\npom = 3"}),
            "result":os.path.join(repo, "feedback.html"),
        }

        response = self.client.post(
            reverse("api_server:execute"),
            data=data
        )
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], 0)
        self.assertEqual(int(response["execution"][0]["stdout"]), 100)
        self.assertTrue("result" in response)

    def test_response_wrong_answer(self):
        id = self.push_frozen_activity(self.activity_data, [self.pl_data1])
        response = self._start_activity(data={
            "path_command":".",
            "command":["python3 start.py activity.json output.json result.json"],
            "frozen_resource_id":id,
        })

        repo = response['execution'][0]['stdout']
        env = response['environment']

        data={
            "path_command":repo,
            "command":["python3 grader.py pl.json answers.json processed.json feedback.html 2> stderr.log"],
            "env_id":env,
            "answer":json.dumps({"answer": ""}),
            "result":os.path.join(repo, "feedback.html"),
        }

        response = self.client.post(
            reverse("api_server:execute"),
            data=data
        )
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], 0)
        self.assertEqual(int(response["execution"][0]["stdout"]), 0)
        self.assertTrue("result" in response)

    def test_next(self):
        id = self.push_frozen_activity(self.activity_data, [self.pl_data1, self.pl_data2])
        response = self._start_activity(data={
            "path_command":".",
            "command":["python3 start.py activity.json output.json result.json"],
            "frozen_resource_id":id,
        })

        env = response['environment']

        data={
            "path_command":".",
            "command":["python3 next.py activity.json output.json result.json"],
            "env_id":env,
            "result":"result.json",
        }

        response = self.client.post(
            reverse("api_server:execute"),
            data=data
        )
        response = json.loads(response.content.decode())

        print(f"RESPONSE = {response}")

        self.assertEqual(response["status"], 0)
        self.assertTrue("result" in response)
