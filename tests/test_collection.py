"""集合加载、环境变量展开、expect 断言的测试。"""

import json
import os
import tempfile
import threading
import unittest
import socketserver
from http.server import BaseHTTPRequestHandler

from httpeek.collection import load_collection, run_collection
from httpeek.errors import HttpPeekError


class _LocalHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        b = b'{"url":"https://x.test/a","ok":true}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)
    def log_message(self, *a):
        pass


class TestCollection(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.f = os.path.join(self.tmp, "c.json")
        self.srv = socketserver.TCPServer(("127.0.0.1", 0), _LocalHandler)
        self.port = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()

    def _write(self, col):
        with open(self.f, "w", encoding="utf-8") as fh:
            json.dump(col, fh)

    def test_load(self):
        self._write({"requests": [{"method": "GET", "path": "/"}]})
        c = load_collection(self.f)
        self.assertEqual(len(c["requests"]), 1)

    def test_load_missing(self):
        with self.assertRaises(FileNotFoundError):
            load_collection(os.path.join(self.tmp, "nope.json"))

    def test_load_invalid_shape(self):
        bad = os.path.join(self.tmp, "bad.json")
        with open(bad, "w", encoding="utf-8") as fh:
            fh.write('{"foo": 1}')
        with self.assertRaises(ValueError):
            load_collection(bad)

    def test_env_expansion(self):
        os.environ["MY_HOST"] = f"http://127.0.0.1:{self.port}"
        try:
            self._write({"base_url": "${MY_HOST}", "requests": [
                {"name": "a", "method": "GET", "path": "/"}]})
            results = run_collection(load_collection(self.f), quiet=True)
            self.assertEqual(results[0]["status"], 200)
        finally:
            del os.environ["MY_HOST"]

    def test_env_missing_raises(self):
        self._write({"base_url": "${DOES_NOT_EXIST_XYZ}", "requests": [
            {"method": "GET", "path": "/"}]})
        with self.assertRaises(HttpPeekError):
            load_collection(self.f)

    def test_expect_pass(self):
        self._write({"base_url": f"http://127.0.0.1:{self.port}",
                     "requests": [{"method": "GET", "path": "/",
                                   "expect": {"status": 200, "contains": "url"}}]})
        results = run_collection(load_collection(self.f), quiet=True)
        self.assertNotIn("_assert_failed", results[0])

    def test_expect_fail(self):
        self._write({"base_url": f"http://127.0.0.1:{self.port}",
                     "requests": [{"method": "GET", "path": "/",
                                   "expect": {"status": 999}}]})
        results = run_collection(load_collection(self.f), quiet=True)
        self.assertTrue(results[0].get("_assert_failed"))


if __name__ == "__main__":
    unittest.main()
