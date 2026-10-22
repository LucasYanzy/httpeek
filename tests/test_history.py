"""本地请求历史测试（HTTPEEK_HOME 隔离到临时目录）。"""

import os
import tempfile
import unittest

from httpeek import history


class TestHistory(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp()
        self._old = os.environ.get("HTTPEEK_HOME")
        os.environ["HTTPEEK_HOME"] = self.home

    def tearDown(self):
        if self._old is None:
            os.environ.pop("HTTPEEK_HOME", None)
        else:
            os.environ["HTTPEEK_HOME"] = self._old

    def test_append_and_load(self):
        history.append("GET", "https://x.test/a", {"X-T": "1"})
        history.append("POST", "https://x.test/b", None, {"k": 1})
        items = history.load()
        self.assertEqual(len(items), 2)
        self.assertEqual(items[1]["method"], "POST")
        self.assertEqual(items[1]["body"], {"k": 1})

    def test_limit(self):
        for i in range(5):
            history.append("GET", f"https://x.test/{i}")
        self.assertEqual(len(history.load(2)), 2)
        self.assertEqual(len(history.load(0)), 5)

    def test_bytes_body_skipped(self):
        history.append("POST", "https://x.test/f", None, b"\x00\x01")
        self.assertIsNone(history.load()[-1]["body"])

    def test_clear(self):
        history.append("GET", "https://x.test/a")
        self.assertTrue(history.clear())
        self.assertEqual(history.load(), [])

    def test_clear_empty(self):
        self.assertFalse(history.clear())


if __name__ == "__main__":
    unittest.main()
