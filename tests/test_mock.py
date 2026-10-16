"""本地 Mock 服务的测试：路径参数、查询规则、响应模板、延迟。"""

import json
import threading
import unittest
import urllib.request

from httpeek.mock_server import make_server


class TestMock(unittest.TestCase):
    def setUp(self):
        col = {
            "mocks": [
                {"method": "GET", "path": "/hello", "status": 200,
                 "headers": {"Content-Type": "application/json"},
                 "body": {"ok": True}},
                {"method": "POST", "path": "/echo", "status": 201, "body": {"echoed": True}},
                {"method": "GET", "path": "/users/{id}", "status": 200,
                 "headers": {"Content-Type": "application/json"},
                 "body": {"id": "{{request.params.id}}", "q": "{{request.query.v}}"}},
                {"method": "GET", "path": "/search", "status": 200, "query": {"v": "1"},
                 "body": {"hit": True}},
                {"method": "GET", "path": "/slow", "status": 200, "delay": 5, "body": {"ok": 1}},
            ]
        }
        self.httpd = make_server("127.0.0.1", 0, col)
        self.port = self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()

    def _get(self, path, method="GET", data=None, raw=False):
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", data=data, method=method)
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()

    def test_get_mock(self):
        status, body = self._get("/hello")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["ok"], True)

    def test_post_mock(self):
        status, _ = self._get("/echo", method="POST", data=b"{}")
        self.assertEqual(status, 201)

    def test_unmatched_404(self):
        status, _ = self._get("/nope")
        self.assertEqual(status, 404)

    def test_path_param_and_template(self):
        status, body = self._get("/users/42?v=9")
        self.assertEqual(status, 200)
        obj = json.loads(body)
        self.assertEqual(obj["id"], "42")
        self.assertEqual(obj["q"], "9")

    def test_query_rule_match(self):
        status, body = self._get("/search?v=1")
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)["hit"])

    def test_query_rule_mismatch_404(self):
        status, _ = self._get("/search?v=2")
        self.assertEqual(status, 404)

    def test_delay(self):
        import time
        t0 = time.time()
        status, _ = self._get("/slow")
        self.assertEqual(status, 200)
        self.assertGreaterEqual(time.time() - t0, 0.004)


if __name__ == "__main__":
    unittest.main()
