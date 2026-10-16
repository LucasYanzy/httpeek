"""CLI 行为测试。"""

import io
import json
import os
import tempfile
import threading
import unittest
import socketserver
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler

from httpeek import cli


def _local_url(port, path="/"):
    return f"http://127.0.0.1:{port}{path}"


class _H(BaseHTTPRequestHandler):
    def do_GET(self):
        b = b'{"ok":true}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)
    def log_message(self, *a):
        pass


class TestCli(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = socketserver.TCPServer(("127.0.0.1", 0), _H)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def _run(self, args):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cli.main(args)
        return rc, buf.getvalue()

    def test_version(self):
        rc, out = self._run(["version"])
        self.assertEqual(rc, 0)
        self.assertIn("httpeek", out)

    def test_help(self):
        rc, out = self._run(["help"])
        self.assertEqual(rc, 0)
        self.assertIn("用法", out)

    def test_unknown(self):
        rc, _ = self._run(["frobnicate"])
        self.assertEqual(rc, 2)

    def test_init_writes_file(self):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "demo.json")
        rc, _ = self._run(["init", p])
        self.assertEqual(rc, 0)
        self.assertTrue(os.path.exists(p))

    def test_get_against_local(self):
        rc, out = self._run(["get", _local_url(self.port)])
        self.assertEqual(rc, 0)
        self.assertIn("200", out)
        self.assertIn('"ok"', out)

    def test_repeat(self):
        rc, out = self._run(["get", _local_url(self.port), "--repeat", "3"])
        self.assertEqual(rc, 0)
        self.assertIn("⏱", out)
        self.assertIn("重复 3", out)

    def test_only_headers(self):
        rc, out = self._run(["get", _local_url(self.port), "--only-headers"])
        self.assertEqual(rc, 0)
        self.assertIn("Content-Type", out)
        self.assertNotIn('"ok"', out)

    def test_verbose(self):
        rc, out = self._run(["get", _local_url(self.port), "-v"])
        self.assertEqual(rc, 0)
        self.assertIn("> GET", out)
        self.assertIn("Host:", out)

    def test_run_with_strict_ok(self):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "c.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"base_url": _local_url(self.port),
                       "requests": [{"method": "GET", "path": "/",
                                     "expect": {"status": 200}}]}, f)
        rc, _ = self._run(["run", p, "--strict"])
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
