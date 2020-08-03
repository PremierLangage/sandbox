# test_utils.py
#
# Authors:
#   - Coumes Quentin <coumes.quentin@gmail.com>


import io
import os
import tarfile

from django.conf import settings
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.urls import reverse
from django_http_exceptions.exceptions import HTTPExceptions

from .utils import ENV1, ENV2, EnvTestCase, SandboxTestCase, TEST_ENVIRONMENT_ROOT
from .. import utils



class MergeTarGZTestCase(EnvTestCase):
    
    def test_merge_tar_gz_both_none(self):
        self.assertEqual(None, utils.merge_tar_gz(None, None))
    
    
    def test_merge_tar_gz_one_none(self):
        b = io.BytesIO(b"test")
        self.assertEqual(b"test", utils.merge_tar_gz(b, None).read())
        b.seek(0)
        self.assertEqual(b"test", utils.merge_tar_gz(None, b).read())
    
    
    def test_merge_tar_gz(self):
        """
        ENV1
        ├── dir
        │   ├── file1.txt # Contains 'env1'
        │   └── file3.txt # Contains 'both1'
        ├── file1.txt # Contains 'env1'
        └── file3.txt # Contains 'both1'
        
        ENV2
        ├── dir
        │   ├── file2.txt # Contains 'env2'
        │   └── file3.txt # Contains 'both2'
        ├── dir2
        │   └── file2.txt # Contains 'env2'
        ├── file2.txt # Contains 'env2'
        └── file3.txt # Contains 'both2'
        
        Result should be :
        ├── dir
        │   ├── file1.txt # Contains 'env1'
        │   ├── file2.txt # Contains 'env2'
        │   └── file3.txt # Contains 'both1'
        ├── dir2
        │   └── file2.txt # Contains 'env2'
        ├── file1.txt # Contains 'env1'
        ├── file2.txt # Contains 'env2'
        └── file3.txt # Contains 'both1'
        """
        env1 = open(os.path.join(TEST_ENVIRONMENT_ROOT, f"{ENV1}.tgz"), "rb")
        env2 = open(os.path.join(TEST_ENVIRONMENT_ROOT, f"{ENV2}.tgz"), "rb")
        result = utils.merge_tar_gz(env1, env2)
        tar = tarfile.open(fileobj=result, mode="r:gz")
        
        env1.close()
        env2.close()
        
        expected = {
            "",
            "dir",
            "dir/file1.txt",
            "dir/file2.txt",
            "dir/file3.txt",
            "dir2",
            "dir2/file2.txt",
            "file1.txt",
            "file2.txt",
            "file3.txt",
        }
        
        self.assertSetEqual(expected, {t.name for t in tar.getmembers()})
        self.assertEqual(b"env1\n", tar.extractfile("dir/file1.txt").read())
        self.assertEqual(b"env2\n", tar.extractfile("dir/file2.txt").read())
        self.assertEqual(b"both1\n", tar.extractfile("dir/file3.txt").read())
        self.assertEqual(b"env2\n", tar.extractfile("dir2/file2.txt").read())
        self.assertEqual(b"env1\n", tar.extractfile("file1.txt").read())
        self.assertEqual(b"env2\n", tar.extractfile("file2.txt").read())
        self.assertEqual(b"both1\n", tar.extractfile("file3.txt").read())
        
        tar.close()



class GetEnvTestCase(SandboxTestCase):
    
    def test_get_env_ok(self):
        self.assertEqual(
            os.path.join(TEST_ENVIRONMENT_ROOT, f"{ENV1}.tgz"),
            utils.get_env(ENV1)
        )
    
    
    def test_get_env_not_found(self):
        self.assertEqual(None, utils.get_env("unknown"))



class ExtractTestCase(SandboxTestCase):
    
    def test_extract_ok(self):
        self.assertEqual(b"env1\n", utils.extract(ENV1, "dir/file1.txt").read())
    
    
    def test_extract_not_found_env(self):
        with self.assertRaises(HTTPExceptions.NOT_FOUND):
            utils.extract("unknown", "unkown")
    
    
    def test_extract_not_found_file(self):
        with self.assertRaises(HTTPExceptions.NOT_FOUND):
            utils.extract(ENV1, "unkown")



class ExecutedEnvTestCase(SandboxTestCase):
    
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
    
    
    def test_executed_env_not_found(self):
        request = self.factory.post(reverse("sandbox:execute"))
        with self.assertRaises(HTTPExceptions.NOT_FOUND):
            utils.executed_env(request, {"environment": "unknown"})
    
    
    def test_executed_env_only_sandbox(self):
        request = self.factory.post(reverse("sandbox:execute"))
        env_uuid = utils.executed_env(request, {"environment": ENV1})
        
        env1_path = os.path.join(TEST_ENVIRONMENT_ROOT, f"{ENV1}.tgz")
        executed_env_path = os.path.join(TEST_ENVIRONMENT_ROOT, "%s.tgz" % env_uuid)
        with open(env1_path, "rb") as env1, open(executed_env_path, "rb") as executed_env:
            self.assertEqual(env1.read(), executed_env.read())
    
    
    def test_executed_env_only_body(self):
        request = self.factory.post(reverse("sandbox:execute"))
        request.FILES["environment"] = open(os.path.join(TEST_ENVIRONMENT_ROOT, f"{ENV2}.tgz"),
                                            "rb")
        
        env_uuid = utils.executed_env(request, {})
        env2_path = os.path.join(TEST_ENVIRONMENT_ROOT, f"{ENV2}.tgz")
        executed_env_path = os.path.join(TEST_ENVIRONMENT_ROOT, "%s.tgz" % env_uuid)
        with open(env2_path, "rb") as env2, open(executed_env_path, "rb") as executed_env:
            self.assertEqual(env2.read(), executed_env.read())
    
    
    def test_executed_env_sandbox_and_body(self):
        """See 'test_merge_tar_gz()' for information about the tests done."""
        request = self.factory.post(reverse("sandbox:execute"))
        request.FILES["environment"] = open(os.path.join(TEST_ENVIRONMENT_ROOT, f"{ENV1}.tgz"),
                                            "rb")
        
        env_uuid = utils.executed_env(request, {"environment": ENV2})
        
        with tarfile.open(os.path.join(TEST_ENVIRONMENT_ROOT, "%s.tgz" % env_uuid), "r:gz") as tar:
            expected = {
                "",
                "dir",
                "dir/file1.txt",
                "dir/file2.txt",
                "dir/file3.txt",
                "dir2",
                "dir2/file2.txt",
                "file1.txt",
                "file2.txt",
                "file3.txt",
            }
            
            self.assertSetEqual(expected, {t.name for t in tar.getmembers()})
            self.assertEqual(b"env1\n", tar.extractfile("dir/file1.txt").read())
            self.assertEqual(b"env2\n", tar.extractfile("dir/file2.txt").read())
            self.assertEqual(b"both1\n", tar.extractfile("dir/file3.txt").read())
            self.assertEqual(b"env2\n", tar.extractfile("dir2/file2.txt").read())
            self.assertEqual(b"env1\n", tar.extractfile("file1.txt").read())
            self.assertEqual(b"env2\n", tar.extractfile("file2.txt").read())
            self.assertEqual(b"both1\n", tar.extractfile("file3.txt").read())



class ParseenvironTestCase(SimpleTestCase):
    
    def test_parse_environ_ok(self):
        expected = {
            "var1": "value1",
            "var2": "value2",
        }
        config = {
            "environ": expected
        }
        
        self.assertDictEqual(expected, utils.parse_environ(config))
    
    
    def test_parse_environ_none(self):
        self.assertEqual({}, utils.parse_environ({}))
    
    
    def test_parse_environ_not_dict(self):
        config = {
            "environ": 1
        }
        
        with self.assertRaises(HTTPExceptions.BAD_REQUEST):
            utils.parse_environ(config)



class ParseResultPathTestCase(SimpleTestCase):
    
    def test_parse_result_path_ok(self):
        config = {
            "result_path": "result.txt"
        }
        
        self.assertEqual("result.txt", utils.parse_result_path(config))
    
    
    def test_parse_result_path_none(self):
        self.assertEqual(None, utils.parse_result_path({}))
    
    
    def test_parse_result_path_not_str(self):
        config = {
            "result_path": 1
        }
        
        with self.assertRaises(HTTPExceptions.BAD_REQUEST):
            utils.parse_result_path(config)



class ParseSavePathTestCase(SimpleTestCase):
    
    def test_parse_save_ok(self):
        config = {
            "save": True
        }
        
        self.assertEqual(True, utils.parse_save(config))
    
    
    def test_parse_save_default(self):
        self.assertEqual(False, utils.parse_save({}))
    
    
    def test_parse_save_not_str(self):
        config = {
            "save": 1
        }
        
        with self.assertRaises(HTTPExceptions.BAD_REQUEST):
            utils.parse_save(config)



class ContainerCpuTestCase(SimpleTestCase):
    
    @override_settings(DOCKER_PARAMETERS={
        **settings.DOCKER_PARAMETERS, **{"cpuset_cpus": "2-4"},
    })
    def container_cpu_count_hyphen(self):
        self.assertEqual(3, utils.container_cpu_count())
    
    
    @override_settings(DOCKER_PARAMETERS={
        **settings.DOCKER_PARAMETERS, **{"cpuset_cpus": "1,4,7,10"},
    })
    def container_cpu_count_hyphen(self):
        self.assertEqual(4, utils.container_cpu_count())



class ContainerRamSwapTestCase(SimpleTestCase):
    
    @override_settings(DOCKER_PARAMETERS={
        **settings.DOCKER_PARAMETERS, **{
            "mem_limit":     "-1",
            "memswap_limit": "-1"
        },
    })
    def test_container_ram_m1s_swap_m1s(self):
        self.assertEqual((-1, -1), utils.container_ram_swap())
    
    
    @override_settings(DOCKER_PARAMETERS={
        **settings.DOCKER_PARAMETERS, **{
            "mem_limit": -1,
            "memswap_limit": -1
        },
    })
    def test_container_ram_m1_swap_m1(self):
        self.assertEqual((-1, -1), utils.container_ram_swap())
    
    
    @override_settings(DOCKER_PARAMETERS={
        **settings.DOCKER_PARAMETERS, **{
            "mem_limit":     "100m",
            "memswap_limit": "0"
        },
    })
    def test_container_ram_100m_swap_0(self):
        self.assertEqual((100000000, 100000000), utils.container_ram_swap())
    
    
    @override_settings(DOCKER_PARAMETERS={
        **settings.DOCKER_PARAMETERS, **{
            "mem_limit":     "100m",
            "memswap_limit": "100m"
        },
    })
    def test_container_ram_100m_swap_100m(self):
        self.assertEqual((100000000, 0), utils.container_ram_swap())
    
    
    @override_settings(DOCKER_PARAMETERS={
        **settings.DOCKER_PARAMETERS, **{
            "mem_limit":     "100m",
            "memswap_limit": "150m"
        },
    })
    def test_container_ram_100m_swap_150m(self):
        self.assertEqual((100000000, 50000000), utils.container_ram_swap())



class ContainerStorageOptTestCase(SimpleTestCase):
    
    @override_settings(DOCKER_PARAMETERS={
        **settings.DOCKER_PARAMETERS, **{"storage_opt": {"size": "300m"}},
    })
    def test_container_storage_opt_300m(self):
        self.assertEqual(300000000, utils.container_storage_opt())
    
    
    @override_settings(DOCKER_PARAMETERS={
        **settings.DOCKER_PARAMETERS, **{"storage_opt": {"size": -1}},
    })
    def test_container_storage_opt_m1(self):
        self.assertEqual(-1, utils.container_storage_opt())
    
    
    @override_settings(DOCKER_PARAMETERS={
        **settings.DOCKER_PARAMETERS, **{"storage_opt": {"size": "-1"}},
    })
    def test_container_storage_opt_m1s(self):
        self.assertEqual(-1, utils.container_storage_opt())
    
    
    @override_settings(DOCKER_PARAMETERS={
        **settings.DOCKER_PARAMETERS, **{"storage_opt": {"size": "host"}},
    })
    def test_container_storage_opt_host(self):
        self.assertEqual(-1, utils.container_storage_opt())
    
    
    @override_settings(DOCKER_PARAMETERS={})
    def test_container_storage_opt_host(self):
        self.assertEqual(-1, utils.container_storage_opt())
