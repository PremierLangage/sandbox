import json
import os

from random import randint

from django.test.utils import override_settings
from sandbox.tasks import remove_expired_env

from django.test import TestCase
from django.urls import reverse

from api_server.utils import data_to_hash
from api_server.enums import LoaderErrCode
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

        with open(os.path.join(TEST_DATA_ROOT, "basic_pl.json")) as f:
            self.pl_data = json.load(f)

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

@override_settings(ENVIRONMENT_EXPIRATION=1)
class CallSandboxTestCase(TestCase):
    def setUp(self) -> None:
        with open(os.path.join(TEST_DATA_ROOT, "basic_pl.json")) as f:
            self.pl_data = json.load(f)

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

    """
    Tests Play Demo
    """
    def test_play_demo_good_answer(self):
        data = {"data": json.dumps(self.pl_data)}
        
        response = self.client.post(reverse("api_server:play_demo"), data=data)
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], 0)

        data = data={"data":json.dumps({"answer":{"answer": "pim = 1\npam = 2\npom = 3"}, "env_id":response["environment"]})}
        response = self.client.post(reverse("api_server:play_demo"), data=data)
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], 0)
        self.assertEqual(response["execution"][0]["stdout"], "100")

    def test_play_demo_wrong_answer(self):
        data = {"data": json.dumps(self.pl_data)}
        
        response = self.client.post(reverse("api_server:play_demo"), data=data)
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], 0)

        data = {"data":json.dumps({"answer":{"answer": ""}, "env_id":response["environment"]})}
        response = self.client.post(reverse("api_server:play_demo"), data=data)
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], 0)
        self.assertEqual(response["execution"][0]["stdout"], "0")

    def test_play_demo_with_path(self):
        data = {"data": json.dumps(self.pl_data), "path": self.paths[0]}
        
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
            data = {"data": json.dumps(self.pl_data), "path": path}
            
            response = self.client.post(reverse("api_server:play_demo"), data=data)
            response = json.loads(response.content.decode())

            self.assertEqual(response["status"], 0)

            data = {"data":json.dumps({"answer":{"answer": "pim = 1\npam = 2\npom = 3"}, "env_id":response["environment"]}), "path": path}
            response = self.client.post(reverse("api_server:play_demo"), data=data)
            response = json.loads(response.content.decode())

            self.assertEqual(response["status"], 0)
            self.assertEqual(response["execution"][0]["stdout"], "100")
    
    def test_play_demo_data_not_present(self):
        data = {"wrong": json.dumps(self.pl_data)}
        
        response = self.client.post(reverse("api_server:play_demo"), data=data)
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], LoaderErrCode.DATA_NOT_PRESENT)

    def test_play_demo_data_not_valid(self):
        data = {"data": self.pl_data}
        
        response = self.client.post(reverse("api_server:play_demo"), data=data)
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], LoaderErrCode.DATA_NOT_VALID)


    """
    Tests Play Exo
    """
    def _push_frozen(self):
        data = {"data": json.dumps(self.pl_data)}

        response = self.client.post(reverse("api_server:frozen_post"), data=data)
        response = json.loads(response.content.decode())
        return response["result"]["id"]

    def test_play_exo_good_answer(self):
        id = self._push_frozen()
        data = {"data":json.dumps({"resource_id":id})}

        response = self.client.post(reverse("api_server:play_exo"), data=data)
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], 0)

        data = {"data":json.dumps({"answer":{"answer": "pim = 1\npam = 2\npom = 3"}, "env_id":response["environment"]})}
        response = self.client.post(reverse("api_server:play_exo"), data=data)
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], 0)
        self.assertEqual(response["execution"][0]["stdout"], "100")

    def test_play_exo_wrong_answer(self):
        id = self._push_frozen()
        data = {"data":json.dumps({"resource_id":id})}

        response = self.client.post(reverse("api_server:play_exo"), data=data)
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], 0)

        data = {"data":json.dumps({"answer":{"answer": ""}, "env_id":response["environment"]})}
        response = self.client.post(reverse("api_server:play_exo"), data=data)
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], 0)
        self.assertEqual(response["execution"][0]["stdout"], "0")

    def test_play_exo_with_path(self):
        id = self._push_frozen()
        data = {"data":json.dumps({"resource_id":id}), "path": self.paths[0]}

        response = self.client.post(reverse("api_server:play_exo"), data=data)
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], 0)

        data = {"data":json.dumps({"answer":{"answer": "pim = 1\npam = 2\npom = 3"}, "env_id":response["environment"]}), "path": self.paths[0]}
        response = self.client.post(reverse("api_server:play_demo"), data=data)
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], 0)
        self.assertEqual(response["execution"][0]["stdout"], "100")
        self.assertTrue(os.path.exists(os.path.join(ENVIRONMENT_ROOT, f"{response['environment']}.tgz")))

    def test_play_exo_with_many_path(self):
        for path in self.paths:
            id = self._push_frozen()
            data = {"data":json.dumps({"resource_id":id}), "path": path}

            response = self.client.post(reverse("api_server:play_exo"), data=data)
            response = json.loads(response.content.decode())

            self.assertEqual(response["status"], 0)

            data = {"data":json.dumps({"answer":{"answer": "pim = 1\npam = 2\npom = 3"}, "env_id":response["environment"]}), "path": path}
            response = self.client.post(reverse("api_server:play_demo"), data=data)
            response = json.loads(response.content.decode())

            self.assertEqual(response["status"], 0)
            self.assertEqual(response["execution"][0]["stdout"], "100")

            self.assertTrue(os.path.exists(os.path.join(ENVIRONMENT_ROOT, f"{response['environment']}.tgz")))

    def test_play_exo_data_not_present(self):
        id = self._push_frozen()
        data = {"wrong": json.dumps({"resource_id":id})}
        
        response = self.client.post(reverse("api_server:play_exo"), data=data)
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], LoaderErrCode.DATA_NOT_PRESENT)

    def test_play_exo_data_not_valid(self):
        id = self._push_frozen()
        data = {"data": {"resource_id":id}}
        
        response = self.client.post(reverse("api_server:play_exo"), data=data)
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], LoaderErrCode.DATA_NOT_VALID)

    def test_play_exo_without_resource_id(self):
        self._push_frozen()
        data = {"data":json.dumps({})} 

        response = self.client.post(reverse("api_server:play_exo"), data=data)
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], LoaderErrCode.FROZEN_RESOURCE_ID_NOT_PRESENT)
    
    def test_play_exo_with_wrong_resource_id(self):
        id = self._push_frozen()
        data = {"data":json.dumps({"resource_id": id+1})}

        response = self.client.post(reverse("api_server:play_exo"), data=data)
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], LoaderErrCode.FROZEN_RESOURCE_ID_NOT_IN_DB)
