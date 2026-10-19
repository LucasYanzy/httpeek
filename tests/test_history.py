"""请求历史（history）功能测试。

每个用例都把 ``HTTPEEK_HOME`` 指向临时目录，绝不触碰用户真实的 ``~/.httpeek``。
覆盖：追加写入、列表、按编号重放、``--no-history``、以及历史文件损坏时不崩溃。
"""

import io
import json
import os
import shutil
import socketserver
import tempfile
import threading
import unittest
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler

from httpeek import cli, history
from httpeek.errors import HttpPeekError


class _H(BaseHTTPRequestHandler):
    def _reply(self):
        b = json.dumps(
            {"ok": True, "path": self.path, "method": self.command}
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    do_GET = _reply
    do_POST = _reply

    def log_message(self, *a):
        pass


class TestHistory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = socketserver.TCPServer(("127.0.0.1", 0), _H)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self._old_home = os.environ.get("HTTPEEK_HOME")
        os.environ["HTTPEEK_HOME"] = self.tmp

    def tearDown(self):
        if self._old_home is None:
            os.environ.pop("HTTPEEK_HOME", None)
        else:
            os.environ["HTTPEEK_HOME"] = self._old_home
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ---------- helpers ----------

    def _url(self, path="/"):
        return f"http://127.0.0.1:{self.port}{path}"

    def _run(self, args):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cli.main(args)
        return rc, buf.getvalue()

    def _hfile(self):
        return os.path.join(self.tmp, "history.jsonl")

    def _lines(self):
        with open(self._hfile(), encoding="utf-8") as f:
            return [ln for ln in f.read().splitlines() if ln.strip()]

    # ---------- storage ----------

    def test_home_env_selects_dir(self):
        self.assertEqual(history.history_dir(), os.path.abspath(self.tmp))
        self.assertEqual(history.history_path(),
                         os.path.join(os.path.abspath(self.tmp), "history.jsonl"))

    def test_record_appends_jsonl(self):
        history.record("GET", "http://x/a", headers={"A": "1"}, body={"k": "v"})
        history.record("POST", "http://x/b")
        lines = self._lines()
        self.assertEqual(len(lines), 2)
        first = json.loads(lines[0])
        self.assertEqual(first["method"], "GET")
        self.assertEqual(first["url"], "http://x/a")
        self.assertEqual(first["headers"], {"A": "1"})
        self.assertEqual(first["body"], {"k": "v"})
        self.assertIn("timestamp", first)

    def test_record_creates_missing_dir(self):
        nested = os.path.join(self.tmp, "deep", "nested")
        os.environ["HTTPEEK_HOME"] = nested
        history.record("GET", "http://x/n")
        self.assertTrue(os.path.exists(os.path.join(nested, "history.jsonl")))

    def test_send_is_recorded(self):
        rc, _ = self._run(["get", self._url("/sv"), "--quiet"])
        self.assertEqual(rc, 0)
        entries = history.load_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["method"], "GET")
        self.assertIn("/sv", entries[0]["url"])

    def test_load_missing_file_is_empty(self):
        self.assertEqual(history.load_entries(), [])

    # ---------- list ----------

    def test_history_lists_entries(self):
        self._run(["get", self._url("/one"), "--quiet"])
        self._run(["post", self._url("/two"), "-d", '{"n": 1}', "--quiet"])
        rc, out = self._run(["history"])
        self.assertEqual(rc, 0)
        self.assertIn("#1", out)
        self.assertIn("#2", out)
        self.assertIn("/one", out)
        self.assertIn("/two", out)

    def test_history_limit(self):
        for p in ("/a", "/b", "/c"):
            self._run(["get", self._url(p), "--quiet"])
        rc, out = self._run(["history", "-n", "1"])
        self.assertEqual(rc, 0)
        self.assertIn("#3", out)
        self.assertNotIn("#1", out)
        self.assertNotIn("#2", out)

    def test_history_empty_message(self):
        rc, out = self._run(["history"])
        self.assertEqual(rc, 0)
        self.assertIn("还没有历史", out)

    # ---------- replay ----------

    def test_history_replay(self):
        self._run(["get", self._url("/replay-me"), "--quiet"])
        rc, out = self._run(["history", "1"])
        self.assertEqual(rc, 0)
        self.assertIn("200", out)
        self.assertIn("/replay-me", out)

    def test_replay_out_of_range(self):
        rc, out = self._run(["history", "5"])
        self.assertEqual(rc, 1)
        self.assertIn("没有编号", out)

    def test_get_entry_invalid(self):
        with self.assertRaises(HttpPeekError):
            history.get_entry("abc")

    # ---------- --no-history ----------

    def test_no_history_flag(self):
        rc, _ = self._run(["get", self._url("/nope"), "--no-history", "--quiet"])
        self.assertEqual(rc, 0)
        self.assertFalse(os.path.exists(self._hfile()))

    def test_no_history_keeps_existing_entries(self):
        self._run(["get", self._url("/keep"), "--quiet"])
        self._run(["get", self._url("/skip"), "--no-history", "--quiet"])
        entries = history.load_entries()
        self.assertEqual(len(entries), 1)
        self.assertIn("/keep", entries[0]["url"])

    # ---------- corrupt file ----------

    def test_corrupt_file_does_not_crash(self):
        with open(self._hfile(), "w", encoding="utf-8") as f:
            f.write("this is not json\n")
            f.write('{"broken": \n')
            f.write("[1, 2, 3]\n")
            f.write("\n")
            f.write(json.dumps({"timestamp": "t", "method": "GET",
                                "url": "http://x/ok"}) + "\n")
        rc, out = self._run(["history"])
        self.assertEqual(rc, 0)
        self.assertIn("/ok", out)

    def test_fully_corrupt_file(self):
        with open(self._hfile(), "w", encoding="utf-8") as f:
            f.write("garbage\n%%%\n")
        rc, out = self._run(["history"])
        self.assertEqual(rc, 0)
        self.assertIn("还没有历史", out)
        # 损坏之后仍能继续追加，并且新行可被正常解析
        history.record("GET", "http://x/after")
        entries = history.load_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["url"], "http://x/after")

    # ---------- help ----------

    def test_history_help(self):
        rc, out = self._run(["history", "--help"])
        self.assertEqual(rc, 0)
        self.assertIn("history", out)
        self.assertIn("--no-history", out)


if __name__ == "__main__":
    unittest.main()
