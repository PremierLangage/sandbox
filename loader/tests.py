from django.urls.base import resolve
from loader.models import FrozenResource
from django.test import TestCase
from django.urls import reverse

from hashlib import sha1

import json

class FrozenTestCase(TestCase):

    def setUp(self) -> None:
        self.data1 = {"data":"frozen1"}
        self.data2 = {"data":"frozen2"}
        self.data3 = {"data":"frozen3"}
        FrozenResource.objects.create(hash=sha1(str(self.data1).encode()).hexdigest(), data=self.data1)
        FrozenResource.objects.create(hash=sha1(str(self.data2).encode()).hexdigest(), data=self.data2)
        self.frozen1 = '{"hash":"' + sha1(str(self.data1).encode()).hexdigest() + '","data":{"data":"frozen1"},"parent":[]}'
        self.frozen2 = '{"hash":"' + sha1(str(self.data2).encode()).hexdigest() + '","data":{"data":"frozen2"},"parent":[]}'
        self.frozen3 = '{"hash":"' + sha1(str(self.data3).encode()).hexdigest() + '","data":{"data":"frozen3"},"parent":[]}'
        super().setUp()

    def test_get_list(self):
        #response = self.client.get(reverse("loader:frozen-list"))
        #self.assertEqual(response.content.decode(), f'[{self.frozen1},{self.frozen2}]')
        pass

    def test_get_details(self):
        response = self.client.get(reverse('loader:frozen-detail', kwargs={'hash': sha1(str(self.data1).encode()).hexdigest()}))
        self.assertEqual(response.content.decode(), f'{self.frozen1}')

    def test_post_already_present(self):
        response = self.client.post(reverse("loader:post_frozen"), {"data":json.dumps({"data":"frozen1"})})
        response = json.loads(response.content.decode())
        self.assertEqual(response["status"], -1)

    def test_post(self):
        response = self.client.post(reverse("loader:post_frozen"), {"data":json.dumps({"data":"frozen3"})})
        response = json.loads(response.content.decode())
        self.assertEqual(response["status"], 200)
        response = self.client.get(reverse("loader:frozen-list"))
        self.assertEqual(response.content.decode(), f'[{self.frozen1},{self.frozen2},{self.frozen3}]')

    def test_post_with_parent(self):
        pass


