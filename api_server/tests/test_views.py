from api_server.models import FrozenResource
from django.test import TestCase
from django.urls import reverse

from api_server.utils import data_to_hash
from api_server.enums import LoaderErrCode

import json
import os

TEST_DATA_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_data")

class FrozenTestCase(TestCase):

    def setUp(self) -> None:
        self.data1 = {"data":"frozen1"}
        self.data2 = {"data":"frozen2"}
        self.data3 = {"data":"frozen3"}

        self.frozen1 = FrozenResource.objects.create(hash=data_to_hash(self.data1), data=self.data1)
        self.frozen2 = FrozenResource.objects.create(hash=data_to_hash(self.data2), data=self.data2)

        super().setUp()
    
    def test_get(self):
        response = self.client.get(reverse('api_server:frozen_get', args=[self.frozen1.id]))
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], 200)

        frozen = response["frozen"]
        self.assertEqual(frozen["hash"], data_to_hash(self.data1))
        self.assertEqual(frozen["data"], self.data1)
        self.assertEqual(frozen["parent"], [])

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
        self.assertEqual(frozen["parent"], [])

    def test_post_already_present(self):
        data = {"data":json.dumps(self.data1)}
        response = self.client.post(reverse("api_server:frozen_post"), data=data)
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], -1)
        self.assertEqual(response["result"]["hash"], data_to_hash(self.data1))

    def test_post_without_data(self):
        response = self.client.post(reverse("api_server:frozen_post"), data={"hash":data_to_hash(self.data1)})
        response = json.loads(response.content.decode())
        self.assertEqual(response["status"], LoaderErrCode.DATA_NOT_PRESENT)

    def test_post_data_not_valid(self):
        response = self.client.post(reverse("api_server:frozen_post"), data={"data":"data"})
        response = json.loads(response.content.decode())
        self.assertEqual(response["status"], LoaderErrCode.DATA_NOT_VALID)

    def test_post_with_parent(self):
        data = {"data":json.dumps(self.data3), "parent":self.frozen1.id}
        response = self.client.post(reverse("api_server:frozen_post"), data=data)
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], 200)
        self.assertEqual(response["result"]["hash"], data_to_hash(self.data3))
        self.assertEqual(response["result"]["parent"], str(self.frozen1.id))


        response = self.client.get(reverse("api_server:frozen_get", args=[response["result"]["id"]]))
        response = json.loads(response.content.decode())
        self.assertEqual(response["status"], 200)
        frozen = response["frozen"]
        self.assertEqual(frozen["hash"], data_to_hash(self.data3))
        self.assertEqual(frozen["data"], self.data3)
        self.assertEqual(frozen["parent"], [self.frozen1.id])


        response = self.client.get(reverse("api_server:frozen_get", args=[self.frozen1.id]))
        response = json.loads(response.content.decode())
        self.assertEqual(response["status"], 200)
        frozen = response["frozen"]
        self.assertEqual(frozen["hash"], data_to_hash(self.data1))
        self.assertEqual(frozen["data"], self.data1)
        self.assertEqual(frozen["parent"], [])
        self.assertEqual(list(self.frozen1.frozenresource_set.all()), [FrozenResource.objects.get(hash=data_to_hash(self.data3))])

    def test_post_with_wrong_parent(self):
        data = {"data":json.dumps(self.data3), "parent":0}
        response = self.client.post(reverse("api_server:frozen_post"), data=data)
        response = json.loads(response.content.decode())
        self.assertEqual(response["status"], LoaderErrCode.NON_EXISTANT_PARENT)
        self.assertEqual("id" in response["result"], False)

