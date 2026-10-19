"""curl 导入解析器测试（纯标准库）。"""

import unittest

from httpeek.importer import parse_curl


class TestImporter(unittest.TestCase):
    def test_simple_get_with_query(self):
        e, b, w = parse_curl("curl https://example.com/a/b?x=1")
        self.assertEqual(e["method"], "GET")
        self.assertEqual(e["path"], "/a/b")
        self.assertEqual(e["query"], {"x": "1"})
        self.assertEqual(b, "https://example.com")

    def test_post_json(self):
        e, b, w = parse_curl(
            "curl -X POST https://example.com/p "
            "-H 'Content-Type: application/json' -d '{\"a\":1}'")
        self.assertEqual(e["method"], "POST")
        self.assertEqual(e["body"], {"a": 1})
        self.assertEqual(e["headers"]["Content-Type"], "application/json")

    def test_data_infers_post(self):
        e, b, w = parse_curl("curl https://example.com/p -d hello")
        self.assertEqual(e["method"], "POST")
        self.assertEqual(e["body"], "hello")

    def test_headers_and_user_agent(self):
        e, b, w = parse_curl("curl https://example.com/a -H 'X-T: 1' -A 'httpeek/1'")
        self.assertEqual(e["headers"]["X-T"], "1")
        self.assertEqual(e["headers"]["User-Agent"], "httpeek/1")

    def test_ignored_flags_warn(self):
        e, b, w = parse_curl("curl -sS --compressed https://example.com/x")
        self.assertEqual(e["method"], "GET")
        self.assertTrue(any("已忽略" in x for x in w))

    def test_unsupported_flag_warn(self):
        e, b, w = parse_curl("curl --weird-flag https://example.com/x")
        self.assertTrue(any("暂不支持" in x for x in w))

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            parse_curl("")

    def test_no_url_raises(self):
        with self.assertRaises(ValueError):
            parse_curl("curl -X POST")

    def test_scheme_default(self):
        e, b, w = parse_curl("curl example.com/x")
        self.assertEqual(b, "https://example.com")
        self.assertEqual(e["path"], "/x")


if __name__ == "__main__":
    unittest.main()
