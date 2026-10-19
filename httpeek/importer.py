"""从 curl 命令导入，生成 httpeek 集合条目（仅标准库）。"""

import json
import shlex
from urllib.parse import parse_qsl, urlparse

# 这些选项对构建请求无影响，导入时安全忽略
IGNORED = {
    "--compressed", "-L", "--location", "-k", "--insecure",
    "-s", "--silent", "-i", "--include", "-v", "--verbose",
    "--globoff", "-#", "--progress-bar", "-f", "--fail",
}


def parse_curl(cmd):
    """解析一条 curl 命令，返回 (entry, base_url, warnings)。"""
    if not cmd or not cmd.strip():
        raise ValueError("curl 命令为空")
    text = cmd.strip()
    if text.startswith("curl"):
        text = text[len("curl"):].strip()
    try:
        toks = shlex.split(text)
    except ValueError as e:
        raise ValueError(f"无法解析命令：{e}")

    method = None
    url = None
    headers = {}
    data = None
    warnings = []
    i = 0
    while i < len(toks):
        t = toks[i]
        if t in ("-X", "--request"):
            method = toks[i + 1].upper(); i += 2
        elif t in ("-H", "--header"):
            v = toks[i + 1]; i += 2
            if ":" in v:
                k, _, vv = v.partition(":")
                headers[k.strip()] = vv.strip()
        elif t in ("-d", "--data", "--data-raw", "--data-binary", "--data-ascii"):
            data = toks[i + 1]; i += 2
        elif t in ("-A", "--user-agent"):
            headers["User-Agent"] = toks[i + 1]; i += 2
        elif t in ("-b", "--cookie"):
            headers["Cookie"] = toks[i + 1]; i += 2
        elif t in ("-u", "--user"):
            headers["Authorization"] = f"Basic {toks[i + 1]}"
            warnings.append("-u/--user 已写为 Authorization: Basic <原文>，未做 base64 编码")
            i += 2
        elif t == "--url":
            url = toks[i + 1]; i += 2
        elif t in IGNORED:
            warnings.append(f"已忽略选项 {t}")
            i += 1
        elif t.startswith("-"):
            warnings.append(f"暂不支持的选项 {t}（已忽略）")
            i += 1
        else:
            if url is None:
                url = t
            i += 1

    if not url:
        raise ValueError("未找到 URL")

    parsed = urlparse(url if "://" in url else "https://" + url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    query = dict(parse_qsl(parsed.query))
    entry = {"name": f"{method or ('POST' if data else 'GET')} {parsed.path or '/'}",
             "method": method or ("POST" if data is not None else "GET"),
             "path": parsed.path or "/"}
    if query:
        entry["query"] = query
    if headers:
        entry["headers"] = headers
    if data is not None:
        try:
            entry["body"] = json.loads(data)
        except Exception:
            entry["body"] = data
    return entry, base_url, warnings
