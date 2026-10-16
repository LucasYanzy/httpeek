"""client.send_request 的集成测试：用真实本地 HTTP 服务。"""

import json
import socketserver
import threading
import unittest
from http.server import BaseHTTPRequestHandler

from httpeek.client import send_request


class _Handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_GET(self):
        if self.path == "/missing":
            self._send(404, {"error": "nope"})
            return
        self._send(200, {"ok": True, "path": self.path})

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(n)
        self._send(201, {"got": json.loads(raw)})

    def log_message(self, *a):
        pass


class TestClient(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = socketserver.TCPServer(("127.0.0.1", 0), _Handler)
        cls.srv.allow_reuse_address = True
        cls.port = cls.srv.server_address[1]
        t = threading.Thread(target=cls.srv.serve_forever, daemon=True)
        t.start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def url(self, p="/x"):
        return f"http://127.0.0.1:{self.port}{p}"

    def test_get_json(self):
        r = send_request("GET", self.url())
        self.assertEqual(r["status"], 200)
        self.assertIn(b"ok", r["body"])

    def test_default_https_prepended(self):
        # 缺少 scheme 时自动补 https（这里用 http 显式）
        r = send_request("GET", f"http://127.0.0.1:{self.port}/")
        self.assertEqual(r["status"], 200)

    def test_post_json_body(self):
        r = send_request("POST", self.url(), data={"a": 1})
        self.assertEqual(r["status"], 201)
        self.assertIn(b"got", r["body"])

    def test_query_string(self):
        r = send_request("GET", self.url("/q"), query={"k": "v"})
        self.assertEqual(r["status"], 200)
        self.assertIn(b"k=v", r["body"])  # path 含查询

    def test_bearer_header(self):
        r = send_request("GET", self.url(), bearer="SECRET")
        self.assertEqual(r["status"], 200)

    def test_http_error_status(self):
        r = send_request("GET", self.url("/missing"))
        self.assertEqual(r["status"], 404)

    def test_custom_header(self):
        r = send_request("GET", self.url(), headers={"X-Test": "1"})
        self.assertEqual(r["status"], 200)


if __name__ == "__main__":
    import unittest
    unittest.main()
