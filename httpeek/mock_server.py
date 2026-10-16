"""本地 Mock 服务：把集合里的 mocks 当作路由返回。仅标准库。

支持：
- 路径参数  /users/{id}
- 查询规则  mock 里写 "query": {"v": "1"} 才匹配
- 响应模板  body/headers 里可用 {{request.method}} {{request.path}}
            {{request.query.KEY}} {{request.body.KEY}} {{request.params.id}}
- 延迟模拟  "delay": 毫秒
"""

import json
import re
import socketserver
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

from .collection import load_collection

_TPL = re.compile(r"\{\{\s*([^}]+?)\s*\}\}")


def _compile_path(path):
    names = []
    def sub(m):
        names.append(m.group(1))
        return r"([^/]+)"
    rx = re.sub(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", sub, path)
    return re.compile("^" + rx + "$"), names


def _resolve(expr, ctx):
    cur = ctx
    for part in expr.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def _render_template(text, ctx):
    def repl(m):
        val = _resolve(m.group(1).strip(), ctx)
        return "" if val is None else str(val)
    return _TPL.sub(repl, text)


def _tpl_deep(value, ctx):
    if isinstance(value, str):
        return _render_template(value, ctx)
    if isinstance(value, dict):
        return {k: _tpl_deep(v, ctx) for k, v in value.items()}
    if isinstance(value, list):
        return [_tpl_deep(v, ctx) for v in value]
    return value


class MockHandler(BaseHTTPRequestHandler):
    routes = []  # [(method, regex, param_names, spec), ...]
    protocol_version = "HTTP/1.1"

    def _query_ok(self, spec, qd):
        want = spec.get("query")
        if not want:
            return True
        for k, v in want.items():
            if qd.get(k) != str(v):
                return False
        return True

    def _find(self, method, path, qd):
        # 先匹配精确静态路径（无参数），再匹配带路径参数的路由
        for meth, rx, names, spec in self.routes:
            if names or meth.upper() != method.upper():
                continue
            if rx.fullmatch(path) and self._query_ok(spec, qd):
                return spec, {}
        for meth, rx, names, spec in self.routes:
            if not names or meth.upper() != method.upper():
                continue
            m = rx.fullmatch(path)
            if m and self._query_ok(spec, qd):
                return spec, dict(zip(names, m.groups()))
        return None, {}

    def _handle(self):
        method = self.command.upper()
        raw_path = self.path.split("?", 1)[0]
        qd = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query))
        spec, params = self._find(method, raw_path, qd)
        if spec is None:
            body = json.dumps({"error": "no mock", "method": method, "path": raw_path}).encode()
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        # 读取请求体用于模板
        body_obj = None
        try:
            n = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(n) if n else b""
            if raw:
                body_obj = json.loads(raw.decode("utf-8"))
        except Exception:
            body_obj = None
        ctx = {"request": {"method": method, "path": raw_path,
                           "query": qd, "params": params, "body": body_obj or {}}}
        delay = spec.get("delay")
        if isinstance(delay, (int, float)):
            time.sleep(delay / 1000.0)
        status = int(spec.get("status", 200))
        headers = dict(spec.get("headers", {}) or {})
        raw = spec.get("body")
        if isinstance(raw, str):
            raw = _render_template(raw, ctx).encode("utf-8")
        elif isinstance(raw, (dict, list)):
            raw = json.dumps(_tpl_deep(raw, ctx), ensure_ascii=False).encode()
            headers.setdefault("Content-Type", "application/json")
        elif isinstance(raw, (bytes, bytearray)):
            raw = bytes(raw)
        else:
            raw = b""
        self.send_response(status)
        for k, v in headers.items():
            self.send_header(k, str(v))
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        if method != "HEAD":
            self.wfile.write(raw)

    def do_GET(self):     self._handle()
    def do_POST(self):    self._handle()
    def do_PUT(self):     self._handle()
    def do_DELETE(self):  self._handle()
    def do_PATCH(self):   self._handle()
    def do_HEAD(self):    self._handle()
    def do_OPTIONS(self): self._handle()
    def log_message(self, *args):  # 静默
        pass


class ThreadingHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def make_server(host: str, port: int, collection: dict) -> ThreadingHTTPServer:
    routes = []
    for spec in collection.get("mocks", []) or []:
        rx, names = _compile_path(spec.get("path", "/"))
        routes.append((spec.get("method", "GET").upper(), rx, names, spec))
    MockHandler.routes = routes
    return ThreadingHTTPServer((host, port), MockHandler)


def serve_forever(host: str, port: int, collection_path: str):
    col = load_collection(collection_path)
    httpd = make_server(host, port, col)
    httpd.serve_forever()
    return httpd
