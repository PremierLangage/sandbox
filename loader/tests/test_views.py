from loader.models import FrozenResource
from django.test import TestCase
from django.urls import reverse

from loader.utils import data_to_hash

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
        response = self.client.get(reverse('loader:frozen', kwargs={'hash': data_to_hash(self.data1)}))
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], 200)

        frozen = response["frozen"]
        self.assertEqual(frozen["hash"], data_to_hash(self.data1))
        self.assertEqual(frozen["data"], self.data1)
        self.assertEqual(frozen["parent"], [])

    def test_post_already_present(self):
        data = {"data":json.dumps(self.data1)}
        response = self.client.post(reverse("loader:frozen"), data=data)
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], -1)
        self.assertEqual(response["result"], {"hash":data_to_hash(self.data1)})
    
    def test_post(self):
        data = {"data":json.dumps(self.data3)}
        response = self.client.post(reverse("loader:frozen"), data=data)
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], 200)
        self.assertEqual(response["result"], {"hash":data_to_hash(self.data3)})

        response = self.client.get(reverse("loader:frozen", kwargs={'hash': data_to_hash(self.data3)}))
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], 200)

        frozen = response["frozen"]
        self.assertEqual(frozen["hash"], data_to_hash(self.data3))
        self.assertEqual(frozen["data"], self.data3)
        self.assertEqual(frozen["parent"], [])

    def test_post_with_parent(self):
        data = {"data":json.dumps(self.data3), "parent":data_to_hash(self.data1)}
        response = self.client.post(reverse("loader:frozen"), data=data)
        response = json.loads(response.content.decode())

        self.assertEqual(response["status"], 200)
        self.assertEqual(response["result"], {"hash":data_to_hash(self.data3),"parent":data_to_hash(self.data1)})


        response = self.client.get(reverse("loader:frozen", kwargs={'hash': data_to_hash(self.data3)}))
        response = json.loads(response.content.decode())
        self.assertEqual(response["status"], 200)
        frozen = response["frozen"]
        self.assertEqual(frozen["hash"], data_to_hash(self.data3))
        self.assertEqual(frozen["data"], self.data3)
        self.assertEqual(frozen["parent"], [data_to_hash(self.data1)])


        response = self.client.get(reverse("loader:frozen", kwargs={'hash': data_to_hash(self.data1)}))
        response = json.loads(response.content.decode())
        self.assertEqual(response["status"], 200)
        frozen = response["frozen"]
        self.assertEqual(frozen["hash"], data_to_hash(self.data1))
        self.assertEqual(frozen["data"], self.data1)
        self.assertEqual(frozen["parent"], [])
        self.assertEqual(list(self.frozen1.frozenresource_set.all()), [FrozenResource.objects.get(hash=data_to_hash(self.data3))])

    def test_post_with_wrong_parent(self):
        data = {"data":json.dumps(self.data3), "parent":data_to_hash({"wrong":"wrong"})}
        response = self.client.post(reverse("loader:frozen"), data=data)
        response = json.loads(response.content.decode())
        self.assertEqual(response["status"], -3)

        response = self.client.get(reverse("loader:frozen", kwargs={'hash': data_to_hash(self.data3)}))
        response = json.loads(response.content.decode())
        self.assertEqual(response["status"], -4)

