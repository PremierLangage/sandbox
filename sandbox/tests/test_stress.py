import json
import os
import random
import threading
import time
from queue import Queue

from django.conf import settings
from django.test import Client, override_settings
from django.urls import reverse

from sandbox.containers import Sandbox
from sandbox.tests.utils import RESOURCES_ROOT, SandboxTestCase


def execute(queue: Queue, test_data: dict, index: int):
    config = test_data["config"]
    environment = test_data.get("environment")
    
    data = {"config": json.dumps(config)}
    if environment is not None:
        data["environment"] = open(os.path.join(settings.ENVIRONMENT_ROOT, environment), "rb")
    
    client = Client()
    response = client.post(reverse("sandbox:execute"), data)
    queue.put((response, index))


@override_settings(WAIT_FOR_CONTAINER_DURATION=3)
class StressTestCase(SandboxTestCase):
    
    def test_stress_same_time(self):
        with open(os.path.join(RESOURCES_ROOT, "stress_test_matrix.json")) as f:
            matrix = json.load(f)
        
        n = len(matrix) - 1
        count = int(settings.DOCKER_COUNT)
        queue = Queue(count)
        threads = list()
        for i in range(count):
            index = random.randint(0, n)
            threads.append(threading.Thread(
                target=execute,
                args=(queue, matrix[index], index)
            ))
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join(10)
        
        for response, i in queue.queue:
            self.assertEqual(response.status_code, 200)
            result = json.loads(response.content.decode())
            self.assertEqual(matrix[i]["expected"], result["result"])
        
        time.sleep(2)
        self.assertEqual(settings.DOCKER_COUNT, Sandbox.available())
    
    
    def test_stress_over_time(self):
        with open(os.path.join(RESOURCES_ROOT, "stress_test_matrix.json")) as f:
            matrix = json.load(f)
        
        n = len(matrix) - 1
        queue = Queue()
        threads = list()
        for i in range(200):
            time.sleep(random.uniform(0.5, 2))
            index = random.randint(0, n)
            t = threading.Thread(
                target=execute,
                args=(queue, matrix[index], index)
            )
            t.start()
            threads.append(t)
            print(i + 1, "/", 200)
        
        for t in threads:
            t.join(10)
        
        for response, i in queue.queue:
            self.assertEqual(response.status_code, 200)
            result = json.loads(response.content.decode())
            self.assertEqual(matrix[i]["expected"], result["result"])
        
        time.sleep(1)
        self.assertEqual(settings.DOCKER_COUNT, Sandbox.available())
