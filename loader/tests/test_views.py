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
    
    def test_get_list(self):
        response = self.client.get(reverse("loader:frozen-list"))
        response = json.loads(response.content.decode())

        fr1 = response[0]
        self.assertEqual(fr1["hash"], self.frozen1.hash)
        self.assertEqual(fr1["data"], self.frozen1.data)
        self.assertEqual(fr1["parent"], list(self.frozen1.parent.all()))


        fr2 = response[1]
        self.assertEqual(fr2["hash"], self.frozen2.hash)
        self.assertEqual(fr2["data"], self.frozen2.data)
        self.assertEqual(fr2["parent"], list(self.frozen2.parent.all()))

    def test_get_details(self):
        response = self.client.get(reverse('loader:frozen-detail', kwargs={'hash': data_to_hash(self.data1)}))
        
        fr1 = json.loads(response.content.decode())
        self.assertEqual(fr1["hash"], self.frozen1.hash)
        self.assertEqual(fr1["data"], self.frozen1.data)
        self.assertEqual(fr1["parent"], list(self.frozen1.parent.all()))

    def test_post_already_present(self):
        data = {"data":json.dumps(self.data1)}
        response = self.client.post(reverse("loader:post_frozen"), data=data)
        response = json.loads(response.content.decode())
        self.assertEqual(response["status"], -1)
        self.assertEqual(response["result"], {"hash":data_to_hash(self.data1)})

    def test_post(self):
        data = {"data":json.dumps(self.data3)}
        response = self.client.post(reverse("loader:post_frozen"), data=data)
        response = json.loads(response.content.decode())
        self.assertEqual(response["status"], 200)
        self.assertEqual(response["result"], {"hash":data_to_hash(self.data3)})

        response = self.client.get(reverse("loader:frozen-list"))
        response = json.loads(response.content.decode())

        fr1 = response[0]
        self.assertEqual(fr1["hash"], self.frozen1.hash)
        self.assertEqual(fr1["data"], self.frozen1.data)
        self.assertEqual(fr1["parent"], list(self.frozen1.parent.all()))

        fr2 = response[1]
        self.assertEqual(fr2["hash"], self.frozen2.hash)
        self.assertEqual(fr2["data"], self.frozen2.data)
        self.assertEqual(fr2["parent"], list(self.frozen2.parent.all()))

        fr3 = response[2]
        self.assertEqual(fr3["hash"], data_to_hash(self.data3))
        self.assertEqual(fr3["data"], self.data3)
        self.assertEqual(fr3["parent"], [])

    def test_post_with_parent(self):
        data = {"data":json.dumps(self.data3), "parent":data_to_hash(self.data1)}
        response = self.client.post(reverse("loader:post_frozen"), data=data)
        response = json.loads(response.content.decode())
        self.assertEqual(response["status"], 200)
        self.assertEqual(response["result"], {"hash":data_to_hash(self.data3),"parent":data_to_hash(self.data1)})

        response = self.client.get(reverse("loader:frozen-detail", kwargs={'hash': data_to_hash(self.data3)}))
        fr3 = json.loads(response.content.decode())
        self.assertEqual(fr3["hash"], data_to_hash(self.data3))
        self.assertEqual(fr3["data"], self.data3)
        self.assertEqual(fr3["parent"], [self.frozen1.hash])

        response = self.client.get(reverse("loader:frozen-detail", kwargs={'hash': data_to_hash(self.data1)}))
        fr1 = json.loads(response.content.decode())
        self.assertEqual(fr1["hash"], self.frozen1.hash)
        self.assertEqual(fr1["data"], self.data1)
        self.assertEqual(fr1["parent"], [])
        self.assertEqual(list(self.frozen1.frozenresource_set.all()), [FrozenResource.objects.get(hash=fr3["hash"])])

    def test_post_with_wrong_parent(self):
        data = {"data":json.dumps(self.data3), "parent":data_to_hash({"wrong":"wrong"})}
        response = self.client.post(reverse("loader:post_frozen"), data=data)
        response = json.loads(response.content.decode())
        self.assertEqual(response["status"], -3)

        response = self.client.get(reverse("loader:frozen-detail", kwargs={'hash': data_to_hash(self.data3)}))
        self.assertEqual(response.content.decode(), '{"detail":"Not found."}')

