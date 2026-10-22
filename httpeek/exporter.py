"""把请求导出成 curl 命令（与 importer 对称，仅标准库）。"""

import json
import shlex


def to_curl(method="GET", url="", headers=None, body=None, bearer=None, form=None):
    """构造与 httpeek 请求等价的 curl 命令。

    form 为 [(name, value), ...] 时用 -F 表达 multipart。
    """
    method = (method or "GET").upper()
    parts = ["curl"]
    if method != "GET":
        parts += ["-X", method]
    hdrs = {}
    if headers:
        hdrs.update(headers)
    if bearer:
        hdrs["Authorization"] = f"Bearer {bearer}"
    for k, v in hdrs.items():
        parts += ["-H", f"{k}: {v}"]
    if form:
        for k, v in form:
            parts += ["-F", f"{k}={v}"]
    elif body is not None:
        if isinstance(body, (dict, list)):
            data = json.dumps(body, ensure_ascii=False)
        elif isinstance(body, (bytes, bytearray)):
            data = body.decode("utf-8", "replace")
        else:
            data = str(body)
        parts += ["-d", data]
    parts.append(url)
    return " ".join(shlex.quote(p) for p in parts)
