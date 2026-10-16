"""集合文件加载与执行（JSON，纯文件、本地优先）。"""

import json
import os
import re

from .client import send_request
from .errors import HttpPeekError
from .pretty import bold, red, green, gray, status_color

# 环境变量占位符用 ${NAME}（与 Mock 模板的 {{...}} 区分，避免冲突）
_ENV_RE = re.compile(r"\$\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}")


def _expand(value):
    """把字符串里的 ${NAME} 替换成环境变量；缺失则明确报错。"""
    if isinstance(value, str):
        def repl(m):
            name = m.group(1)
            if name not in os.environ:
                raise HttpPeekError(
                    f"集合引用了环境变量 ${{{name}}}，但当前环境不存在。"
                    f"请先 `export {name}=...` 或在运行前设置。"
                )
            return os.environ[name]
        return _ENV_RE.sub(repl, value)
    if isinstance(value, dict):
        return {k: _expand(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand(v) for v in value]
    return value


def load_collection(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"集合文件不存在：{path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or "requests" not in data:
        raise ValueError("集合文件需包含 'requests' 数组")
    return _expand(data)


def _check_expect(req, res):
    expect = req.get("expect")
    if not expect:
        return True, ""
    fails = []
    if "status" in expect and res.get("status") != expect["status"]:
        fails.append(f"期望状态 {expect['status']}，实际 {res.get('status')}")
    if "contains" in expect:
        body = res.get("body", b"")
        if isinstance(body, (bytes, bytearray)):
            body = body.decode("utf-8", "replace")
        if expect["contains"] not in str(body):
            fails.append(f"响应体不包含 {expect['contains']!r}")
    return (len(fails) == 0), "; ".join(fails)


def run_collection(collection, timeout=10, insecure=False, quiet=False, strict=False):
    """按顺序执行集合里的 requests，返回结果列表。"""
    base = collection.get("base_url", "")
    global_headers = collection.get("headers", {}) or {}
    bearer = collection.get("bearer")
    results = []
    failed = 0
    for req in collection["requests"]:
        method = req.get("method", "GET")
        path = req.get("path", "")
        if base and path:
            url = base.rstrip("/") + "/" + path.lstrip("/")
        else:
            url = path or base
        headers = dict(global_headers)
        headers.update(req.get("headers", {}) or {})
        data = req.get("body") if req.get("body") is not None else req.get("data")
        query = req.get("query")
        name = req.get("name", f"{method} {url}")
        if not quiet:
            print(bold(f"▶ {name}"))
        try:
            res = send_request(
                method, url, headers=headers, data=data, query=query,
                bearer=bearer or req.get("bearer"),
                timeout=timeout, insecure=insecure,
            )
            ok, why = _check_expect(req, res)
            if not ok:
                failed += 1
                res["_assert_failed"] = True
            results.append(res)
            if not quiet:
                print("  ", status_color(res["status"]), res["reason"],
                      gray(f"({res['elapsed'] * 1000:.0f}ms)"))
                print("  ", green("✓ 断言通过") if ok else red("✗ 断言失败: ") + why)
        except Exception as e:
            failed += 1
            results.append({"error": str(e), "_assert_failed": True})
            if not quiet:
                print("  ", red("✗"), str(e))
    if strict and failed and not quiet:
        print(red(f"\n{failed} 个请求未通过（--strict）。"))
    return results
