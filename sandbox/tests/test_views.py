import json
import os
import tarfile
import time
import uuid

from django.conf import settings
from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from django_http_exceptions import HTTPExceptions

from sandbox.container import Sandbox
from sandbox.enums import SandboxErrCode
from sandbox.tests.utils import EnvTestCase, SandboxTestCase
from sandbox.utils import ENV1, ENV2



class EnvViewTestCase(EnvTestCase):
    
    def test_head_ok(self):
        response = self.client.head(reverse("sandbox:environment", args=(ENV1,)))
        path = os.path.join(settings.ENVIRONMENT_ROOT, f"{ENV1}.tgz")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Length"], str(os.stat(path).st_size))
        self.assertEqual(response['Content-Type'], "application/gzip")
        self.assertEqual(response['Content-Disposition'], f"attachment; filename={ENV1}.tgz")
    
    
    def test_get_ok(self):
        response = self.client.get(reverse("sandbox:environment", args=(ENV1,)))
        path = os.path.join(settings.ENVIRONMENT_ROOT, f"{ENV1}.tgz")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Length"], str(os.stat(path).st_size))
        self.assertEqual(response['Content-Type'], "application/gzip")
        self.assertEqual(response['Content-Disposition'], f"attachment; filename={ENV1}.tgz")
        
        with open(path, "rb") as f:
            self.assertEqual(f.read(), response.content)
    
    
    def test_head_404(self):
        response = self.client.head(reverse("sandbox:environment", args=(uuid.uuid4(),)))
        self.assertEqual(response.status_code, 404)
    
    
    def test_get_404(self):
        response = self.client.get(reverse("sandbox:environment", args=(uuid.uuid4(),)))
        self.assertEqual(response.status_code, 404)



class FileViewTestCase(EnvTestCase):
    
    def test_head_ok(self):
        response = self.client.head(reverse("sandbox:file", args=(ENV1, "file1.txt")))
        path = os.path.join(settings.ENVIRONMENT_ROOT, f"{ENV1}.tgz")
        
        with tarfile.open(path, "r:gz") as tar:
            size = tar.extractfile("file1.txt").seek(0, os.SEEK_END)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Length"], str(size))
        self.assertEqual(response['Content-Type'], "application/octet-stream")
        self.assertEqual(response['Content-Disposition'], f"attachment; filename=file1.txt")
    
    
    def test_get_ok(self):
        response = self.client.get(reverse("sandbox:file", args=(ENV1, "file1.txt")))
        path = os.path.join(settings.ENVIRONMENT_ROOT, f"{ENV1}.tgz")
        
        with tarfile.open(path, "r:gz") as tar:
            content = tar.extractfile("file1.txt").read()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Length"], str(len(content)))
        self.assertEqual(response['Content-Type'], "application/octet-stream")
        self.assertEqual(response['Content-Disposition'], f"attachment; filename=file1.txt")
        self.assertEqual(content, response.content)
    
    
    def test_head_404_env(self):
        with self.assertRaises(HTTPExceptions.NOT_FOUND):
            self.client.head(reverse("sandbox:file", args=(uuid.uuid4(), "unknown")))
    
    
    def test_get_404_env(self):
        with self.assertRaises(HTTPExceptions.NOT_FOUND):
            self.client.get(reverse("sandbox:file", args=(uuid.uuid4(), "unknown")))
    
    
    def test_head_404_file(self):
        with self.assertRaises(HTTPExceptions.NOT_FOUND):
            self.client.head(reverse("sandbox:file", args=(ENV1, "unknown")))
    
    
    def test_get_404_file(self):
        with self.assertRaises(HTTPExceptions.NOT_FOUND):
            self.client.get(reverse("sandbox:file", args=(ENV1, "unknown")))



class SpecificationsTestCase(SandboxTestCase):
    
    @override_settings(DOCKER_PARAMETERS={
        **settings.DOCKER_PARAMETERS, **{
            "cpuset_cpus": "2,3,4",
            "storage_opt": {},
        }
    })
    def test_specifications_ok(self):
        # Set containers running to 2 and available to DOCKER_COUNT - 2
        Sandbox.acquire()
        Sandbox.acquire()
        
        response = self.client.get(reverse("sandbox:specs"))
        self.assertEqual(response.status_code, 200)
        
        specs = json.loads(response.content.decode())
        self.assertEqual(settings.DOCKER_COUNT, specs["containers"]["total"])
        self.assertEqual(settings.DOCKER_COUNT - 2, specs["containers"]["available"])
        self.assertEqual(2, specs["containers"]["running"])
        self.assertEqual(3, specs["cpu"]["count"])
        self.assertEqual("host", specs["memory"]["storage"])
    
    
    @override_settings(DOCKER_PARAMETERS={
        **settings.DOCKER_PARAMETERS, **{
            "cpuset_cpus": "2-4",
            "storage_opt": {"size": "300m"},
        }
    })
    def test_specifications_ok_other_cpu_storage_opt(self):
        # Set containers running to 2 and available to DOCKER_COUNT - 2
        Sandbox.acquire()
        Sandbox.acquire()
        
        response = self.client.get(reverse("sandbox:specs"))
        self.assertEqual(response.status_code, 200)
        
        specs = json.loads(response.content.decode())
        self.assertEqual(settings.DOCKER_COUNT, specs["containers"]["total"])
        self.assertEqual(settings.DOCKER_COUNT - 2, specs["containers"]["available"])
        self.assertEqual(2, specs["containers"]["running"])
        self.assertEqual(3, specs["cpu"]["count"])
        self.assertEqual("300m", specs["memory"]["storage"])
    
    
    def test_specifications_405(self):
        # Set containers running to 2 and available to DOCKER_COUNT - 2
        response = self.client.post(reverse("sandbox:specs"))
        self.assertEqual(response.status_code, 405)



class LibrariesTestCase(SimpleTestCase):
    
    def test_libraries_ok(self):
        response = self.client.get(reverse("sandbox:libraries"))
        self.assertEqual(response.status_code, 200)
        # Is a valid json
        json.loads(response.content.decode())
    
    
    def test_libraries_405(self):
        # Set containers running to 2 and available to DOCKER_COUNT - 2
        response = self.client.post(reverse("sandbox:libraries"))
        self.assertEqual(response.status_code, 405)



class ExecuteTestCase(SandboxTestCase):
    
    def test_execute_ok_without_env(self):
        data = {
            "config": json.dumps({
                "commands": [
                    "true",
                    {"command": "echo $((1+1))", "timeout": 1},
                    "-false",
                ]
            })
        }
        response = self.client.post(reverse("sandbox:execute"), data)
        self.assertEqual(response.status_code, 200)
        
        result = json.loads(response.content.decode())
        self.assertEqual(0, result["status"])
        self.assertEqual(3, len(result["execution"]))
        self.assertEqual("2", result["execution"][1]["stdout"])
        
        real_total = sum(r["time"] for r in result["execution"])
        self.assertTrue(result["total_time"] - 0.5 <= real_total <= result["total_time"])
    
    
    def test_execute_ok_with_env_config(self):
        data = {
            "config": json.dumps({
                "commands":    [
                    'echo "Hello World !" > result.txt'
                ],
                "environment": ENV1,
                "result_path": "result.txt"
            })
        }
        response = self.client.post(reverse("sandbox:execute"), data)
        self.assertEqual(response.status_code, 200)
        
        result = json.loads(response.content.decode())
        self.assertEqual(0, result["status"])
        self.assertEqual(1, len(result["execution"]))
        self.assertNotIn("environment", result)
        self.assertEqual("Hello World !", result["result"])
        
        real_total = sum(r["time"] for r in result["execution"])
        self.assertTrue(result["total_time"] - 0.5 <= real_total <= result["total_time"])
    
    
    def test_execute_ok_with_env_body_save(self):
        data = {
            "config":      json.dumps({
                "commands":    [
                    'echo "Hello World !" > result.txt'
                ],
                "result_path": "result.txt",
                "save":        True,
            }),
            "environment": open(os.path.join(settings.ENVIRONMENT_ROOT, f"{ENV1}.tgz"), "rb")
        }
        response = self.client.post(reverse("sandbox:execute"), data)
        self.assertEqual(response.status_code, 200)
        
        result = json.loads(response.content.decode())
        self.assertEqual(0, result["status"])
        self.assertEqual(1, len(result["execution"]))
        self.assertIn("environment", result)
        self.assertEqual("Hello World !", result["result"])
        
        real_total = sum(r["time"] for r in result["execution"])
        self.assertTrue(result["total_time"] - 0.5 <= real_total <= result["total_time"])
        
        time.sleep(0.1)  # Wait for the thread saving the env to finish
        path = os.path.join(settings.ENVIRONMENT_ROOT, f"{result['environment']}.tgz")
        self.assertTrue(os.path.isfile(path))
        with tarfile.open(path, "r:gz") as tar:
            expected = {
                "dir",
                "dir/file1.txt",
                "dir/file3.txt",
                "file1.txt",
                "file3.txt",
                "result.txt"
            }
            
            self.assertSetEqual(expected, {t.name for t in tar.getmembers()})
            self.assertEqual(b"env1\n", tar.extractfile("dir/file1.txt").read())
            self.assertEqual(b"both1\n", tar.extractfile("dir/file3.txt").read())
            self.assertEqual(b"env1\n", tar.extractfile("file1.txt").read())
            self.assertEqual(b"both1\n", tar.extractfile("file3.txt").read())
            self.assertEqual(b"Hello World !\n", tar.extractfile("result.txt").read())
    
    
    def test_execute_ok_with_env_config_and_body_save(self):
        data = {
            "config":      json.dumps({
                "commands":    [
                    'echo "Hello World !" > result.txt'
                ],
                "result_path": "result.txt",
                "save":        True,
                "environment": ENV2,
            }),
            "environment": open(os.path.join(settings.ENVIRONMENT_ROOT, f"{ENV1}.tgz"), "rb")
        }
        response = self.client.post(reverse("sandbox:execute"), data)
        self.assertEqual(response.status_code, 200)
        
        result = json.loads(response.content.decode())
        self.assertEqual(0, result["status"])
        self.assertEqual(1, len(result["execution"]))
        self.assertIn("environment", result)
        self.assertEqual("Hello World !", result["result"])
        
        real_total = sum(r["time"] for r in result["execution"])
        self.assertTrue(result["total_time"] - 0.5 <= real_total <= result["total_time"])
        
        time.sleep(0.1)  # Wait for the thread saving the env to finish
        path = os.path.join(settings.ENVIRONMENT_ROOT, f"{result['environment']}.tgz")
        self.assertTrue(os.path.isfile(path))
        with tarfile.open(path, "r:gz") as tar:
            expected = {
                "dir",
                "dir/file1.txt",
                "dir/file2.txt",
                "dir/file3.txt",
                "dir2",
                "dir2/file2.txt",
                "file1.txt",
                "file2.txt",
                "file3.txt",
                "result.txt"
            }
            
            self.assertSetEqual(expected, {t.name for t in tar.getmembers()})
            self.assertEqual(b"env1\n", tar.extractfile("dir/file1.txt").read())
            self.assertEqual(b"env2\n", tar.extractfile("dir/file2.txt").read())
            self.assertEqual(b"both1\n", tar.extractfile("dir/file3.txt").read())
            self.assertEqual(b"env2\n", tar.extractfile("dir2/file2.txt").read())
            self.assertEqual(b"env1\n", tar.extractfile("file1.txt").read())
            self.assertEqual(b"env2\n", tar.extractfile("file2.txt").read())
            self.assertEqual(b"both1\n", tar.extractfile("file3.txt").read())
            self.assertEqual(b"Hello World !\n", tar.extractfile("result.txt").read())
    
    
    def test_execute_ok_with_env_save(self):
        data = {
            "config": json.dumps({
                "commands":    [
                    'echo "Hello World !" > result.txt'
                ],
                "environment": ENV1,
                "save":        True,
                "result_path": "result.txt"
            })
        }
        response = self.client.post(reverse("sandbox:execute"), data)
        self.assertEqual(response.status_code, 200)
        
        result = json.loads(response.content.decode())
        self.assertEqual(0, result["status"])
        self.assertEqual(1, len(result["execution"]))
        self.assertEqual("Hello World !", result["result"])
        
        real_total = sum(r["time"] for r in result["execution"])
        self.assertTrue(result["total_time"] - 0.5 <= real_total <= result["total_time"])
        
        time.sleep(0.1)  # Wait for the thread saving the env to finish
        path = os.path.join(settings.ENVIRONMENT_ROOT, f"{result['environment']}.tgz")
        self.assertTrue(os.path.isfile(path))
        with tarfile.open(path, "r:gz") as tar:
            expected = {
                "dir",
                "dir/file1.txt",
                "dir/file3.txt",
                "file1.txt",
                "file3.txt",
                "result.txt"
            }
            
            self.assertSetEqual(expected, {t.name for t in tar.getmembers()})
            self.assertEqual(b"env1\n", tar.extractfile("dir/file1.txt").read())
            self.assertEqual(b"both1\n", tar.extractfile("dir/file3.txt").read())
            self.assertEqual(b"env1\n", tar.extractfile("file1.txt").read())
            self.assertEqual(b"both1\n", tar.extractfile("file3.txt").read())
            self.assertEqual(b"Hello World !\n", tar.extractfile("result.txt").read())
    
    
    def test_execute_ok_environ(self):
        data = {
            "config": json.dumps({
                "commands":    [
                    'echo $VAR1'
                ],
                "environ":     {
                    "VAR1": "My var"
                },
                "environment": ENV1,
            })
        }
        response = self.client.post(reverse("sandbox:execute"), data)
        self.assertEqual(response.status_code, 200)
        
        result = json.loads(response.content.decode())
        self.assertEqual(0, result["status"])
        self.assertEqual(1, len(result["execution"]))
        self.assertEqual("My var", result["execution"][0]["stdout"])
    
    
    def test_execute_timeout(self):
        data = {
            "config": json.dumps({
                "commands": [
                    {"command": "echo $((1+1))", "timeout": 1},
                    {"command": "sleep 1", "timeout": 0.2},
                ],
            })
        }
        response = self.client.post(reverse("sandbox:execute"), data)
        self.assertEqual(response.status_code, 200)
        
        result = json.loads(response.content.decode())
        self.assertEqual(SandboxErrCode.TIMEOUT, result["status"])
        self.assertEqual("sleep 1", result["execution"][1]["command"])
        self.assertEqual(SandboxErrCode.TIMEOUT, result["execution"][1]["exit_code"])
        self.assertEqual("", result["execution"][1]["stdout"])
        self.assertEqual(f"Sandbox timed out after 0.2 seconds\n", result["execution"][1]["stderr"])
        self.assertIsInstance(result["execution"][1]["time"], float)
        self.assertLessEqual(result["execution"][1]["time"], 0.21)
    
    
    def test_execute_failing(self):
        data = {
            "config": json.dumps({
                "commands": [
                    "false"
                ],
            })
        }
        response = self.client.post(reverse("sandbox:execute"), data)
        self.assertEqual(response.status_code, 200)
        
        result = json.loads(response.content.decode())
        self.assertEqual(1, len(result["execution"]))
        real_total = sum(r["time"] for r in result["execution"])
        self.assertTrue(result["total_time"] - 0.5 <= real_total <= result["total_time"])
    
    
    def test_execute_result_not_found(self):
        data = {
            "config": json.dumps({
                "commands":    [
                    "true"
                ],
                "result_path": "unknown.txt"
            })
        }
        response = self.client.post(reverse("sandbox:execute"), data)
        self.assertEqual(response.status_code, 200)
        
        result = json.loads(response.content.decode())
        self.assertEqual(SandboxErrCode.RESULT_NOT_FOUND, result["status"])
        self.assertEqual(1, len(result["execution"]))
    
    
    def test_execute_405(self):
        response = self.client.get(reverse("sandbox:execute"))
        self.assertEqual(response.status_code, 405)
    
    
    def test_execute_missing_config(self):
        response = self.client.post(reverse("sandbox:execute"))
        self.assertEqual(response.status_code, 400)
    
    
    def test_execute_config_not_json(self):
        data = {
            "config": "Definitely not json"
        }
        response = self.client.post(reverse("sandbox:execute"), data=data)
        self.assertEqual(response.status_code, 400)
    
    
    def test_execute_config_not_dict(self):
        data = {
            "config": json.dumps("Definitely not json")
        }
        response = self.client.post(reverse("sandbox:execute"), data=data)
        self.assertEqual(response.status_code, 400)
