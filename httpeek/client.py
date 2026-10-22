"""HTTP 请求发送（仅标准库）。"""

import json
import os
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

from .errors import HttpPeekError


def build_multipart(fields):
    """把 [(name, value), ...] 构造成 multipart/form-data。

    value 以 '@' 开头表示文件上传（@./a.txt）。
    返回 (body_bytes, content_type)。
    """
    boundary = "----httpeek" + uuid.uuid4().hex
    parts = []
    for name, value in fields:
        if value.startswith("@"):
            path = value[1:]
            with open(path, "rb") as f:
                content = f.read()
            filename = os.path.basename(path)
            head = (f'--{boundary}\r\n'
                    f'Content-Disposition: form-data; name="{name}"; '
                    f'filename="{filename}"\r\n'
                    f'Content-Type: application/octet-stream\r\n\r\n')
            parts.append(head.encode("utf-8") + content + b"\r\n")
        else:
            head = f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n'
            parts.append(head.encode("utf-8") + value.encode("utf-8") + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def _build_url(url: str, query):
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    if query:
        parts = urllib.parse.urlparse(url)
        q = dict(urllib.parse.parse_qsl(parts.query))
        q.update(query)
        url = parts._replace(query=urllib.parse.urlencode(q, doseq=True)).geturl()
    return url


def send_request(method="GET", url="", headers=None, data=None, query=None,
                 bearer=None, timeout=10, insecure=False):
    """发送一次 HTTP 请求，返回结构化结果字典。"""
    method = (method or "GET").upper()
    url = _build_url(url, query)
    hdrs = {}
    if headers:
        hdrs.update(headers)
    if bearer:
        hdrs["Authorization"] = f"Bearer {bearer}"

    body = None
    if data is not None:
        if isinstance(data, (dict, list)):
            body = json.dumps(data).encode("utf-8")
            hdrs.setdefault("Content-Type", "application/json")
        elif isinstance(data, str):
            body = data.encode("utf-8")
        elif isinstance(data, (bytes, bytearray)):
            body = bytes(data)
        else:
            body = str(data).encode("utf-8")

    req = urllib.request.Request(url, data=body, method=method)
    for k, v in hdrs.items():
        req.add_header(k, v)

    ctx = None
    if insecure:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            status = resp.status
            reason = resp.reason
            raw_headers = list(resp.getheaders())
            resp_headers = dict(raw_headers)
            raw = resp.read()
    except urllib.error.HTTPError as e:
        status = e.code
        reason = e.reason
        raw_headers = list(e.headers.items()) if e.headers else []
        resp_headers = dict(raw_headers)
        raw = e.read()
    except urllib.error.URLError as e:
        raise HttpPeekError(f"无法连接到 {url}：{e.reason}")
    except TimeoutError:
        raise HttpPeekError(f"请求超时（>{timeout}s）：{url}")

    set_cookies = [v for k, v in raw_headers if k.lower() == "set-cookie"]

    return {
        "method": method,
        "url": url,
        "status": status,
        "reason": reason or "",
        "headers": resp_headers,
        "set_cookies": set_cookies,
        "body": raw,
        "elapsed": time.time() - start,
    }
