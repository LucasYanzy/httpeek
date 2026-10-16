#!/usr/bin/env python3
"""httpeek 离线演示：启动本地 Mock，然后用 httpeek 自身发起请求。

运行：python demo/demo.py
完全离线、零依赖、零账号——证明"零配置能跑出结果"。
"""

import os
import sys
import json
import tempfile
import threading
import time

# 让脚本能 import 到 httpeek 包（仓库根目录）
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from httpeek.mock_server import make_server
from httpeek.client import send_request
from httpeek.pretty import bold, cyan, green, red, status_color, format_body


COLLECTION = {
    "mocks": [
        {"method": "GET", "path": "/hello", "status": 200,
         "headers": {"Content-Type": "application/json"},
         "body": {"message": "你好，这是 httpeek 的本地 Mock 响应", "ok": True}},
        {"method": "POST", "path": "/echo", "status": 201,
         "headers": {"Content-Type": "application/json"},
         "body": {"echoed": True}},
        {"method": "GET", "path": "/users/{id}", "status": 200,
         "headers": {"Content-Type": "application/json"},
         "body": {"id": "{{request.params.id}}", "q": "{{request.query.v}}"}},
    ]
}


def main():
    httpd = make_server("127.0.0.1", 0, COLLECTION)
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{port}"
    time.sleep(0.3)

    print(bold("① 启动本地 Mock："), cyan(base), green("✓"))
    print(bold("② GET ") + base + "/hello")
    r = send_request("GET", base + "/hello")
    print("  ", status_color(r["status"]), r["reason"])
    print(format_body(r["body"], r["headers"].get("Content-Type", "")))

    print(bold("③ POST ") + base + "/echo")
    r = send_request("POST", base + "/echo", data={})
    print("  ", status_color(r["status"]), r["reason"])
    print(format_body(r["body"], r["headers"].get("Content-Type", "")))

    print(bold("④ GET ") + base + "/nope （未匹配路由）")
    r = send_request("GET", base + "/nope")
    print("  ", status_color(r["status"]), r["reason"])

    print(bold("⑤ GET ") + base + "/users/42?v=9 （路径参数 + 响应模板）")
    r = send_request("GET", base + "/users/42?v=9")
    print("  ", status_color(r["status"]), r["reason"])
    print(format_body(r["body"], r["headers"].get("Content-Type", "")))

    httpd.shutdown()
    print(green("\n✓ 演示结束。真实使用：httpeek mock your.json 常驻，再 httpeek get <url>。"))


if __name__ == "__main__":
    main()
