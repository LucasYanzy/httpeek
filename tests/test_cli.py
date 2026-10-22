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
        cls._old_home = os.environ.get("HTTPEEK_HOME")
        cls._home = tempfile.mkdtemp()
        os.environ["HTTPEEK_HOME"] = cls._home  # 隔离历史，不写用户目录
        cls.srv = socketserver.TCPServer(("127.0.0.1", 0), _H)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()
        if cls._old_home is None:
            os.environ.pop("HTTPEEK_HOME", None)
        else:
            os.environ["HTTPEEK_HOME"] = cls._old_home

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

    def test_save_to_collection(self):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "c.json")
        rc, out = self._run(["get", _local_url(self.port, "/sv"), "--save", p])
        self.assertEqual(rc, 0)
        self.assertIn("已保存", out)
        with open(p, encoding="utf-8") as f:
            col = json.load(f)
        self.assertEqual(col["requests"][0]["path"], "/sv")
        self.assertTrue(col["base_url"].startswith("http://127.0.0.1"))
        # 再存一条，应追加而非覆盖
        self._run(["get", _local_url(self.port, "/sv2"), "--save", p])
        with open(p, encoding="utf-8") as f:
            col2 = json.load(f)
        self.assertEqual(len(col2["requests"]), 2)

    def test_import_command(self):
        rc, out = self._run(["import", "curl -X POST https://httpbin.org/post -d hello"])
        self.assertEqual(rc, 0)
        self.assertIn("POST", out)
        self.assertIn("/post", out)

    def test_import_with_save(self):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "c.json")
        rc, _ = self._run(["import", "curl -X POST https://httpbin.org/post -d hello",
                           "--save", p])
        self.assertEqual(rc, 0)
        with open(p, encoding="utf-8") as f:
            col = json.load(f)
        self.assertEqual(col["requests"][0]["method"], "POST")

    def test_multipart_builder(self):
        from httpeek.client import build_multipart
        d = tempfile.mkdtemp()
        fp = os.path.join(d, "a.txt")
        with open(fp, "w", encoding="utf-8") as f:
            f.write("hello-file")
        body, ctype = build_multipart([("name", "a"), ("f", "@" + fp)])
        self.assertIn("multipart/form-data; boundary=", ctype)
        boundary = ctype.split("boundary=")[1]
        txt = body.decode("utf-8", errors="replace")
        self.assertIn('name="name"', txt)
        self.assertIn('filename="a.txt"', txt)
        self.assertIn("hello-file", txt)
        self.assertIn(boundary, txt)


    def test_to_curl_no_send(self):
        rc, out = self._run(["get", _local_url(self.port), "--to-curl"])
        self.assertEqual(rc, 0)
        self.assertIn("curl", out)
        self.assertNotIn("→", out)  # 未实际发送

    def test_to_curl_post_body(self):
        rc, out = self._run(["post", _local_url(self.port), "-d", '{"a":1}', "--to-curl"])
        self.assertEqual(rc, 0)
        self.assertIn("-X POST", out)

    def test_history_record_and_list(self):
        self._run(["get", _local_url(self.port, "/hist")])
        rc, out = self._run(["history"])
        self.assertEqual(rc, 0)
        self.assertIn("/hist", out)

    def test_history_replay(self):
        self._run(["get", _local_url(self.port, "/replay")])
        rc, out = self._run(["history", "1"])
        self.assertEqual(rc, 0)
        self.assertIn("200", out)

    def test_history_clear(self):
        self._run(["get", _local_url(self.port, "/c")])
        rc, out = self._run(["history", "--clear"])
        self.assertEqual(rc, 0)
        self.assertIn("已清空", out)

    def test_save_and_send_cookies(self):
        from http.server import BaseHTTPRequestHandler

        class C(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path.startswith("/set"):
                    self.send_response(200)
                    self.send_header("Set-Cookie", "sid=42; Path=/")
                    self.end_headers()
                    return
                body = json.dumps({"cookie": self.headers.get("Cookie", "")}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            def log_message(self, *a):
                pass

        srv = socketserver.TCPServer(("127.0.0.1", 0), C)
        port = srv.server_address[1]
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            jar = os.path.join(tempfile.mkdtemp(), "jar.json")
            rc, _ = self._run(["get", _local_url(port, "/set"), "--save-cookies", jar])
            self.assertEqual(rc, 0)
            self.assertTrue(os.path.exists(jar))
            rc, out = self._run(["get", _local_url(port, "/check"), "--cookies", jar])
            self.assertEqual(rc, 0)
            self.assertIn("sid=42", out)
        finally:
            srv.shutdown(); srv.server_close()

    def test_multipart_builder(self):
        from httpeek.client import build_multipart
        d = tempfile.mkdtemp()
        fp = os.path.join(d, "a.txt")
        with open(fp, "w", encoding="utf-8") as f:
            f.write("hello-file")
        body, ctype = build_multipart([("name", "a"), ("f", "@" + fp)])
        self.assertIn("multipart/form-data; boundary=", ctype)
        boundary = ctype.split("boundary=")[1]
        txt = body.decode("utf-8", errors="replace")
        self.assertIn('name="name"', txt)
        self.assertIn('filename="a.txt"', txt)
        self.assertIn("hello-file", txt)
        self.assertIn(boundary, txt)


if __name__ == "__main__":
    unittest.main()
