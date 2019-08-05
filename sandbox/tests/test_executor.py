import os
import tarfile
import time

from django.conf import settings
from django_http_exceptions import HTTPExceptions

from sandbox.utils import ENV1
from ..container import Sandbox
from ..enums import SandboxErrCode
from ..executor import Command, Executor
from ..tests.utils import SandboxTestCase



class CommandTestCase(SandboxTestCase):
    
    def test_check_ok(self):
        self.assertTrue(Command._check({"command": "true"}))
        self.assertTrue(Command._check({"command": "true", "timeout": 1}))
        self.assertTrue(Command._check({"command": "true", "timeout": 1.0}))
    
    
    def test_check_wrong_command(self):
        self.assertFalse(Command._check({}))
        self.assertFalse(Command._check({"timeout": 1}))
        self.assertFalse(Command._check({"command": object()}))
        self.assertFalse(Command._check({"command": object(), "timeout": 1}))
    
    
    def test_check_timeout_wrong(self):
        self.assertFalse(Command._check({"command": "true", "timeout": object()}))
    
    
    def test_from_request_ok(self):
        config = {
            "commands": [
                "true",
                {"command": "true"},
                {"command": "-false", "timeout": 1},
                {"command": "true", "timeout": 1},
            ]
        }
        commands = Command.from_config(config)
        self.assertEqual("true", commands[0].command)
        self.assertEqual("true", commands[1].command)
        self.assertEqual("false", commands[2].command)
        self.assertEqual("true", commands[3].command)
        self.assertEqual(settings.EXECUTE_TIMEOUT, commands[0].timeout)
        self.assertEqual(settings.EXECUTE_TIMEOUT, commands[1].timeout)
        self.assertEqual(1, commands[2].timeout)
        self.assertEqual(1, commands[3].timeout)
        self.assertEqual(False, commands[0].ignore_failure)
        self.assertEqual(False, commands[1].ignore_failure)
        self.assertEqual(True, commands[2].ignore_failure)
        self.assertEqual(False, commands[3].ignore_failure)
    
    
    def test_from_request_missing(self):
        with self.assertRaises(HTTPExceptions.BAD_REQUEST):
            Command.from_config({})
    
    
    def test_from_request_command_not_list(self):
        with self.assertRaises(HTTPExceptions.BAD_REQUEST):
            Command.from_config({})
    
    
    def test_from_request_bad_commands(self):
        with self.assertRaises(HTTPExceptions.BAD_REQUEST):
            Command.from_config({"commands": object()})
    
    
    def test_from_request_bad_command(self):
        with self.assertRaises(HTTPExceptions.BAD_REQUEST):
            Command.from_config({"commands": [object()]})
    
    
    def test_execute_ok(self):
        s = Sandbox.acquire()
        
        status, result = Command("echo $((1+1))").execute(s.container)
        
        self.assertTrue(status)
        self.assertEqual("echo $((1+1))", result["command"])
        self.assertEqual(0, result["exit_code"])
        self.assertEqual("2", result["stdout"])
        self.assertEqual("", result["stderr"])
        self.assertIsInstance(result["time"], float)
    
    
    def test_execute_ignore_failure(self):
        s = Sandbox.acquire()
        status, result = Command("-false").execute(s.container)
        
        self.assertTrue(status)
        self.assertEqual("false", result["command"])
        self.assertEqual(1, result["exit_code"])
        self.assertEqual("", result["stdout"])
        self.assertEqual("", result["stderr"])
        self.assertIsInstance(result["time"], float)
    
    
    def test_execute_timeout(self):
        s = Sandbox.acquire()
        status, result = Command("echo $((1+1))", timeout=1).execute(s.container)
        
        self.assertTrue(status)
        self.assertEqual("echo $((1+1))", result["command"])
        self.assertEqual(0, result["exit_code"])
        self.assertEqual("2", result["stdout"])
        self.assertEqual("", result["stderr"])
        self.assertIsInstance(result["time"], float)
        
        status, result = Command("sleep 1", timeout=0.2).execute(s.container)
        self.assertFalse(status)
        self.assertEqual("sleep 1", result["command"])
        self.assertEqual(SandboxErrCode.TIMEOUT, result["exit_code"])
        self.assertEqual("", result["stdout"])
        self.assertEqual(f"Sandbox timed out after 0.2 seconds\n", result["stderr"])
        self.assertIsInstance(result["time"], float)
        self.assertLessEqual(result["time"], 0.25)



class ExecutorTestCase(SandboxTestCase):
    
    def test_execute_ok_without_env(self):
        commands = [
            Command("true"),
            Command("echo $((1+1))", timeout=1),
            Command("-false"),
        ]
        s = Sandbox.acquire()
        e = Executor(commands, s)
        
        result = e.execute()
        self.assertEqual(0, result["status"])
        self.assertEqual(3, len(result["execution"]))
        
        real_total = sum(r["time"] for r in result["execution"])
        self.assertTrue(result["total_time"] - 0.5 <= real_total <= result["total_time"])
    
    
    def test_execute_ok_with_env_save(self):
        commands = [
            Command('echo "Hello World !" > result.txt')
        ]
        s = Sandbox.acquire()
        e = Executor(commands, s, env_uuid=ENV1, result="result.txt", save=True)
        
        result = e.execute()
        self.assertEqual(0, result["status"])
        self.assertEqual(1, len(result["execution"]))
        self.assertEqual(e.env_uuid, result["environment"])
        self.assertEqual("Hello World !", result["result"])
        
        real_total = sum(r["time"] for r in result["execution"])
        self.assertTrue(result["total_time"] - 0.5 <= real_total <= result["total_time"])
        
        path = os.path.join(settings.ENVIRONMENT_ROOT, result["environment"] + ".tgz")
        time.sleep(0.1)  # Wait for the thread saving the env to finish
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
    
    
    def test_execute_ok_with_env_no_save(self):
        commands = [
            Command('echo "Hello World !" > result.txt')
        ]
        s = Sandbox.acquire()
        e = Executor(commands, s, env_uuid=ENV1, result="result.txt")
        
        result = e.execute()
        self.assertEqual(0, result["status"])
        self.assertEqual(1, len(result["execution"]))
        self.assertNotIn("environment", result)
        self.assertEqual("Hello World !", result["result"])
        
        real_total = sum(r["time"] for r in result["execution"])
        self.assertTrue(result["total_time"] - 0.5 <= real_total <= result["total_time"])
    
    
    def test_execute_ok_environ(self):
        s = Sandbox.acquire()
        e = Executor([Command('echo $VAR1', environ={"VAR1": "My var"})], s)
        
        result = e.execute()
        self.assertEqual(0, result["status"])
        self.assertEqual(1, len(result["execution"]))
        self.assertEqual("My var", result["execution"][0]["stdout"])
    
    
    def test_execute_failing(self):
        s = Sandbox.acquire()
        e = Executor([Command("false")], s)
        
        result = e.execute()
        self.assertEqual(1, result["status"])
        self.assertEqual(1, len(result["execution"]))
        real_total = sum(r["time"] for r in result["execution"])
        self.assertTrue(result["total_time"] - 0.5 <= real_total <= result["total_time"])
    
    
    def test_execute_result_not_found(self):
        s = Sandbox.acquire()
        e = Executor([Command("true")], s, result="unknown.txt")
        
        result = e.execute()
        self.assertEqual(SandboxErrCode.RESULT_NOT_FOUND, result["status"])
        self.assertEqual(1, len(result["execution"]))
