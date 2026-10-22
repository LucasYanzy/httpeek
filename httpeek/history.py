"""本地请求历史（JSONL 存储，仅标准库，绝不上传）。"""

import json
import os
import time


def _home():
    return os.environ.get("HTTPEEK_HOME") or os.path.join(
        os.path.expanduser("~"), ".httpeek")


def path():
    return os.path.join(_home(), "history.jsonl")


def append(method, url, headers=None, body=None):
    """追加一条请求记录（二进制 body 不记录）。"""
    if isinstance(body, (bytes, bytearray)):
        body = None
    entry = {
        "ts": int(time.time()),
        "method": (method or "GET").upper(),
        "url": url,
        "headers": headers or {},
        "body": body,
    }
    p = path()
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load(limit=20):
    p = path()
    if not os.path.exists(p):
        return []
    out = []
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out[-limit:] if limit else out


def clear():
    p = path()
    if os.path.exists(p):
        os.remove(p)
        return True
    return False
