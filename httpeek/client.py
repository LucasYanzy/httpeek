"""HTTP 请求发送（仅标准库）。"""

import json
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request

from .errors import HttpPeekError


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
            resp_headers = dict(resp.getheaders())
            raw = resp.read()
    except urllib.error.HTTPError as e:
        status = e.code
        reason = e.reason
        resp_headers = dict(e.headers.items()) if e.headers else {}
        raw = e.read()
    except urllib.error.URLError as e:
        raise HttpPeekError(f"无法连接到 {url}：{e.reason}")
    except TimeoutError:
        raise HttpPeekError(f"请求超时（>{timeout}s）：{url}")

    return {
        "method": method,
        "url": url,
        "status": status,
        "reason": reason or "",
        "headers": resp_headers,
        "body": raw,
        "elapsed": time.time() - start,
    }
