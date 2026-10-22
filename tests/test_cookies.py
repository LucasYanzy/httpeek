"""Cookie / 会话保持测试（JSON jar，纯标准库）。"""

import os
import tempfile
import unittest

from httpeek import cookies


class TestCookies(unittest.TestCase):
    def setUp(self):
        self.p = os.path.join(tempfile.mkdtemp(), "jar.json")

    def test_parse_basic(self):
        c = cookies.parse_set_cookie("session=abc; Path=/; HttpOnly")
        self.assertEqual(c["name"], "session")
        self.assertEqual(c["value"], "abc")
        self.assertEqual(c["path"], "/")
        self.assertTrue(c["httponly"])

    def test_parse_domain_secure(self):
        c = cookies.parse_set_cookie("a=1; Domain=.example.com; Secure; Max-Age=60")
        self.assertEqual(c["domain"], "example.com")
        self.assertTrue(c["secure"])
        self.assertEqual(c["max-age"], "60")

    def test_parse_invalid(self):
        self.assertIsNone(cookies.parse_set_cookie("garbage"))

    def test_update_and_header(self):
        cookies.update(self.p, ["sid=42; Domain=example.com; Path=/"], "example.com")
        jar = cookies.load_jar(self.p)
        self.assertEqual(jar[0]["name"], "sid")
        self.assertEqual(cookies.header_for(jar, "www.example.com"), "sid=42")
        self.assertEqual(cookies.header_for(jar, "evil.com"), "")

    def test_update_replaces_same_name(self):
        cookies.update(self.p, ["sid=1; Domain=example.com"], "example.com")
        cookies.update(self.p, ["sid=2; Domain=example.com"], "example.com")
        jar = cookies.load_jar(self.p)
        self.assertEqual(len(jar), 1)
        self.assertEqual(cookies.header_for(jar, "example.com"), "sid=2")

    def test_default_domain_from_host(self):
        cookies.update(self.p, ["a=1"], "127.0.0.1:8080")
        jar = cookies.load_jar(self.p)
        self.assertEqual(jar[0]["domain"], "127.0.0.1")

    def test_empty_update_noop(self):
        cookies.update(self.p, [], "x.test")
        self.assertEqual(cookies.load_jar(self.p), [])


if __name__ == "__main__":
    unittest.main()
