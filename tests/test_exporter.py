"""导出为 curl 命令的测试。"""

import unittest

from httpeek.exporter import to_curl


class TestExporter(unittest.TestCase):
    def test_get(self):
        self.assertEqual(to_curl("GET", "https://x.test/a"), "curl https://x.test/a")

    def test_post_json(self):
        c = to_curl("POST", "https://x.test/a", body={"k": 1})
        self.assertIn("-X POST", c)
        self.assertIn("-d", c)
        self.assertIn('{"k": 1}', c)

    def test_headers_quoted(self):
        c = to_curl("GET", "https://x.test/a", headers={"X-T": "1 2"})
        self.assertIn("'X-T: 1 2'", c)

    def test_bearer(self):
        c = to_curl("GET", "https://x.test/a", bearer="tok")
        self.assertIn("Authorization: Bearer tok", c)

    def test_form(self):
        c = to_curl("POST", "https://x.test/a", form=[("name", "a"), ("f", "@./a.txt")])
        self.assertIn("-F", c)
        self.assertIn("name=a", c)
        self.assertIn("f=@./a.txt", c)


if __name__ == "__main__":
    unittest.main()
