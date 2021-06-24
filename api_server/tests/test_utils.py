from django.test import TestCase

from api_server.utils import *

from sandbox.containers import initialise_containers, purging_containers

class UtilsTestCase(TestCase):
    def setUp(self) -> None:
        purging_containers()
        super().setUp()

    def tearDown(self) -> None:
        super().tearDown()

    def test_data_to_hash(self):
        hash = sha1(str("str").encode()).hexdigest()
        data_hash = data_to_hash("str")
        self.assertEqual(str, type(data_hash))
        self.assertEqual(hash, data_hash)

    def test_tar_from_dic(self):
        dic = {
            "key1.txt":"key1",
            "key2.txt":"key2",
            "key3.pdf":"key3",
        }
        tar = tar_from_dic(dic)

        with tarfile.open(fileobj=io.BytesIO(tar), mode="r:gz") as t:
            count_file = 0
            for member in t.getmembers():
                if member.isfile():
                    f=t.extractfile(member)
                    content=f.read().decode().rstrip('\n')
                    self.assertEqual(dic[member.name], content)
                    count_file += 1

            self.assertEqual(len(dic), count_file)

    def test_create_seed(self):
        for i in range(100):
            seed = create_seed()
            self.assertLessEqual(0, seed)
            self.assertGreaterEqual(99, seed)
        
    def test_build_pl_with_seed(self):
        seed = 100
        pl_data = {"seed":seed}
        build_pl(pl_data)
        self.assertEqual(seed, pl_data["seed"])

    def test_build_pl_without_seed(self):
        pl_data = {}
        build_pl(pl_data)
        self.assertLessEqual(0, pl_data["seed"])
        self.assertGreaterEqual(99, pl_data["seed"])

    def test_build_pl_with_param(self):
        pl_data = {"un":1, "deux":2}
        build_pl(pl_data=pl_data, params={"deux":"deux", "trois":3})
        self.assertEqual(pl_data["un"], 1)
        self.assertEqual(pl_data["deux"], "deux")
        self.assertEqual(pl_data["trois"], 3)

    def test_build_pl_with_settings(self):
        pl_data = {"un":1, "deux":2}
        build_pl(pl_data=pl_data, settings={"deux":"deux", "trois":3})
        self.assertEqual(pl_data["un"], 1)
        self.assertEqual(pl_data["deux"], "deux")
        self.assertEqual(pl_data["trois"], 3)
