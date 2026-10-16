"""httpeek 命令行入口：方法即命令，子命令 run/mock/init/ai。"""

import json
import os
import sys

from . import __version__
from .ai import generate_request, AiUnavailable, DEFAULT_MODEL, OLLAMA_URL
from .client import send_request
from .collection import load_collection, run_collection
from .mock_server import make_server
from .pretty import (
    bold, red, green, cyan, dim, gray, status_color, format_body,
)

METHODS = {"get", "post", "put", "delete", "patch", "head", "options"}

SAMPLE_COLLECTION = {
    "name": "示例集合（可自行删改）",
    "base_url": "https://httpbin.org",
    "headers": {"Accept": "application/json"},
    "requests": [
        {"name": "echo GET", "method": "GET", "path": "/get", "query": {"hello": "world"}},
        {"name": "echo POST", "method": "POST", "path": "/post", "body": {"title": "httpeek", "done": False}},
        {"name": "健康检查(断言示例)", "method": "GET", "path": "/get",
         "expect": {"status": 200, "contains": "url"}},
    ],
    "mocks": [
        {"method": "GET", "path": "/hello", "status": 200,
         "headers": {"Content-Type": "application/json"},
         "body": {"message": "你好，这是 httpeek 的本地 Mock 响应", "ok": True}},
        {"method": "POST", "path": "/echo", "status": 201,
         "headers": {"Content-Type": "application/json"},
         "body": {"echoed": True}},
        {"method": "GET", "path": "/users/{id}", "status": 200,
         "headers": {"Content-Type": "application/json"},
         "body": {"id": "{{request.params.id}}", "from": "{{request.path}}",
                  "q": "{{request.query.v}}"}},
    ],
}


def _parse_opts(args):
    opts = {"headers": {}, "data": None, "query": {}, "bearer": None,
            "timeout": 10, "insecure": False, "output": None, "json_out": False,
            "verbose": False, "quiet": False, "only_headers": False,
            "only_body": False, "repeat": 1, "_req_headers": {}}
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--no-color":
            os.environ["NO_COLOR"] = "1"
        elif a == "--insecure":
            opts["insecure"] = True
        elif a == "--json":
            opts["json_out"] = True
        elif a in ("-t", "--timeout"):
            opts["timeout"] = float(args[i + 1]); i += 1
        elif a in ("-o", "--output"):
            opts["output"] = args[i + 1]; i += 1
        elif a in ("-H", "--header"):
            kv = args[i + 1]; i += 1
            if ":" in kv:
                k, _, v = kv.partition(":")
                opts["headers"][k.strip()] = v.strip()
        elif a in ("-q", "--query"):
            kv = args[i + 1]; i += 1
            if "=" in kv:
                k, _, v = kv.partition("=")
                opts["query"][k.strip()] = v.strip()
        elif a == "--bearer":
            opts["bearer"] = args[i + 1]; i += 1
        elif a in ("-d", "--data"):
            val = args[i + 1]; i += 1
            s = val.strip()
            if s[:1] in ("{", "["):
                try:
                    opts["data"] = json.loads(val)
                except Exception:
                    opts["data"] = val
            else:
                opts["data"] = val
        elif a in ("-v", "--verbose"):
            opts["verbose"] = True
        elif a == "--only-headers":
            opts["only_headers"] = True
        elif a == "--only-body":
            opts["only_body"] = True
        elif a == "--quiet":
            opts["quiet"] = True
        elif a in ("-r", "--repeat"):
            opts["repeat"] = int(args[i + 1]); i += 1
        i += 1
    return opts


def _emit(res, opts):
    if opts.get("verbose"):
        from urllib.parse import urlparse
        p = urlparse(res["url"])
        print(dim("> ") + bold(f"{res['method']} {p.path or '/'} HTTP/1.1"))
        print(dim("> ") + f"Host: {p.netloc}")
        for k, v in opts.get("_req_headers", {}).items():
            print(dim("> ") + f"{k}: {v}")
        print()
    if opts.get("only_headers"):
        _print_resp_headers(res)
        return
    if opts.get("only_body"):
        print(format_body(res.get("body", b""), res.get("headers", {}).get("Content-Type", "")))
        return
    print(bold("→"), status_color(res["status"]), res["reason"],
          gray(f"({res['elapsed'] * 1000:.0f} ms)"), dim(res["url"]))
    for k, v in res.get("headers", {}).items():
        if k.lower() in ("content-type", "content-length"):
            print(gray(f"  {k}: {v}"))
    print()
    print(format_body(res.get("body", b""), res.get("headers", {}).get("Content-Type", "")))


def _print_resp_headers(res):
    for k, v in res.get("headers", {}).items():
        print(f"{k}: {v}")


def _print_stats(times):
    n = len(times)
    avg = sum(times) / n * 1000
    mn = min(times) * 1000
    mx = max(times) * 1000
    print(dim(f"⏱ 重复 {n} 次：平均 {avg:.1f}ms，最快 {mn:.1f}ms，最慢 {mx:.1f}ms"))


def _print_response(res):
    _emit(res, {})


def _print_help():
    print("""httpeek __VERSION__ — 终端 HTTP 客户端 + 内置 Mock（零依赖）

用法:
  httpeek <method> <url> [选项]     发送一次请求（method: get/post/put/delete/patch/head/options）
  httpeek run <file.json>           按顺序执行集合里的请求
  httpeek mock <file.json>          把集合里的 mocks 当作本地 Mock 服务
  httpeek init [file.json]          生成一份示例集合
  httpeek ai "<自然语言>" [--run]   用本机 Ollama 生成请求（可选直接发送）
  httpeek version                   查看版本

请求选项:
  -H, --header K:V       请求头，可重复（如 -H "Authorization: Bearer x"）
  -d, --data JSON/文本    请求体；以 { } 或 [ ] 开头按 JSON 解析
  -q, --query k=v        查询参数，可重复
  --bearer TOKEN         Authorization: Bearer
  -t, --timeout 秒       超时（默认 10）
  -o, --output 文件      把响应体写入文件
  -v, --verbose          同时打印请求行与请求头
  --only-headers         只打印响应头
  --only-body            只打印响应体
  --quiet                静默（只返回退出码，便于脚本）
  -r, --repeat N         重复发送 N 次并打印耗时统计
  --json                 以 JSON 输出结果（便于管道处理）
  --insecure             跳过 TLS 证书校验
  --no-color             关闭彩色

集合（run/mock）支持:
  ${ENV}                请求/响应里引用环境变量（如 ${TOKEN}）
  expect                请求条目可加 "expect":{"status":200,"contains":"ok"} 做断言
  mock 路径参数          "/users/{id}" 匹配 /users/42
  mock 响应模板          body 里用 {{request.path}} {{request.query.k}} {{request.body.k}}
  mock 查询规则          "query":{"v":"1"} 仅当查询匹配时路由
  mock 延迟              "delay": 毫秒，模拟网络延迟

示例:
  httpeek get https://api.github.com/repos/octocat/Hello-World
  httpeek post https://httpbin.org/post -d '{"name":"httpeek"}' -H "X-Token: 1"
  httpeek get https://api.github.com/zen -v --only-body
  httpeek get https://httpbin.org/get -r 5
  httpeek init demo.json && httpeek mock demo.json
  httpeek get http://127.0.0.1:8080/hello        # 配合上面的 mock
  httpeek get http://127.0.0.1:8080/users/42     # 路径参数 + 模板
  httpeek run demo.json --strict                  # 带断言的冒烟测试
  httpeek ai "获取北京天气" --model qwen2.5:latest --run

零依赖、零账号、可离线（mock 模式）。详见 README。""".replace("__VERSION__", __version__))


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("help", "-h", "--help"):
        _print_help()
        return 0
    if argv[0] in ("version", "-v", "--version"):
        print("httpeek " + __version__)
        return 0

    head = argv[0].lower()

    if head in METHODS:
        if len(argv) < 2:
            print(red("缺少 URL，例如：httpeek get https://example.com"))
            return 2
        method = head.upper()
        url = argv[1]
        opts = _parse_opts(argv[2:])
        req_headers = dict(opts["headers"])
        if opts["bearer"]:
            req_headers["Authorization"] = f"Bearer {opts['bearer']}"
        opts["_req_headers"] = req_headers
        repeat = max(1, int(opts["repeat"]))
        times = []
        last = None
        try:
            for _ in range(repeat):
                last = send_request(
                    method, url, headers=opts["headers"], data=opts["data"],
                    query=opts["query"], bearer=opts["bearer"],
                    timeout=opts["timeout"], insecure=opts["insecure"],
                )
                times.append(last["elapsed"])
        except Exception as e:
            print(red("✗"), str(e))
            return 1
        if opts["json_out"]:
            out = {
                "status": last["status"], "headers": last["headers"],
                "body": last["body"].decode("utf-8", "replace"),
            }
            if repeat > 1:
                out["stats"] = {"count": repeat,
                                "avg_ms": round(sum(times) / repeat * 1000, 2),
                                "min_ms": round(min(times) * 1000, 2),
                                "max_ms": round(max(times) * 1000, 2)}
            print(json.dumps(out, ensure_ascii=False))
            return 0
        if opts["quiet"]:
            return 0
        if repeat > 1:
            _print_stats(times)
        _emit(last, opts)
        if opts["output"]:
            with open(opts["output"], "wb") as f:
                f.write(last["body"])
            print(dim(f"已保存到 {opts['output']}"))
        return 0

    if head == "run":
        if len(argv) < 2:
            print(red("缺少集合文件，例如：httpeek run demo.json")); return 2
        opts = _parse_opts(argv[2:])
        strict = "--strict" in argv[2:]
        try:
            col = load_collection(argv[1])
        except Exception as e:
            print(red("✗"), str(e)); return 1
        results = run_collection(col, timeout=opts["timeout"], insecure=opts["insecure"], strict=strict)
        if strict and any(r.get("_assert_failed") for r in results):
            return 1
        return 0

    if head == "mock":
        if len(argv) < 2:
            print(red("缺少集合文件，例如：httpeek mock demo.json")); return 2
        host, port = "127.0.0.1", 8080
        rest = argv[2:]
        i = 0
        while i < len(rest):
            a = rest[i]
            if a == "--host":
                host = rest[i + 1]; i += 1
            elif a == "--port":
                port = int(rest[i + 1]); i += 1
            i += 1
        try:
            col = load_collection(argv[1])
        except Exception as e:
            print(red("✗"), str(e)); return 1
        try:
            httpd = make_server(host, port, col)
        except OSError as e:
            print(red("✗"), f"无法在 {host}:{port} 启动：{e}"); return 1
        print(bold("httpeek mock 已启动："), cyan(f"http://{host}:{port}"))
        print(dim("按 Ctrl+C 停止。可用 `httpeek get http://" + f"{host}:{port}" + "/hello` 试一下。"))
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n已停止。")
        return 0

    if head == "init":
        path = argv[1] if len(argv) > 1 else "httpeek.json"
        if os.path.exists(path):
            print(red(f"文件已存在：{path}")); return 1
        with open(path, "w", encoding="utf-8") as f:
            json.dump(SAMPLE_COLLECTION, f, ensure_ascii=False, indent=2)
        print(green("✓"), f"已生成示例集合：{path}")
        print(dim(f"下一步：httpeek run {path} 或 httpeek mock {path}"))
        return 0

    if head == "ai":
        if len(argv) < 2:
            print(red("缺少自然语言描述，例如：httpeek ai \"获取北京天气\"")); return 2
        prompt = argv[1]
        model, base, do_run = DEFAULT_MODEL, OLLAMA_URL, False
        rest = argv[2:]
        i = 0
        while i < len(rest):
            a = rest[i]
            if a == "--model":
                model = rest[i + 1]; i += 1
            elif a == "--url":
                base = rest[i + 1]; i += 1
            elif a == "--run":
                do_run = True
            i += 1
        try:
            spec = generate_request(prompt, model=model, base_url=base)
        except AiUnavailable as e:
            print(red("✗"), str(e)); return 1
        print(bold("生成请求："))
        print(json.dumps(spec, ensure_ascii=False, indent=2))
        if do_run:
            try:
                res = send_request(
                    spec.get("method", "GET"), spec.get("url"),
                    headers=spec.get("headers"), data=spec.get("body"), timeout=20,
                )
                _print_response(res)
            except Exception as e:
                print(red("✗"), str(e)); return 1
        return 0

    print(red(f"未知命令：{argv[0]}"))
    _print_help()
    return 2
