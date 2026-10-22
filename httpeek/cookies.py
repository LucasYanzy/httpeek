"""Cookie / 会话保持（JSON 存储，仅标准库）。"""

import json
import os


def parse_set_cookie(header: str):
    parts = [p.strip() for p in (header or "").split(";") if p.strip()]
    if not parts or "=" not in parts[0]:
        return None
    name, value = parts[0].split("=", 1)
    c = {"name": name.strip(), "value": value.strip()}
    for p in parts[1:]:
        low = p.lower()
        if low == "httponly":
            c["httponly"] = True
        elif low == "secure":
            c["secure"] = True
        elif "=" in p:
            k, v = p.split("=", 1)
            k = k.strip().lower()
            v = v.strip()
            if k == "domain":
                c["domain"] = v.lstrip(".")
            elif k == "path":
                c["path"] = v
            elif k in ("expires", "max-age"):
                c[k] = v
    return c


def load_jar(path: str):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_jar(path: str, jar):
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(jar, f, ensure_ascii=False, indent=2)


def update(path: str, set_cookie_headers, host: str):
    """把响应里的 Set-Cookie 写回 jar 文件。"""
    if not set_cookie_headers:
        return
    jar = load_jar(path)
    default_domain = host.split(":")[0] if host else ""
    for h in set_cookie_headers:
        c = parse_set_cookie(h)
        if not c:
            continue
        c.setdefault("domain", default_domain)
        c.setdefault("path", "/")
        jar = [x for x in jar if not (
            x.get("name") == c["name"]
            and x.get("domain") == c["domain"]
            and x.get("path", "/") == c.get("path", "/")
        )]
        jar.append(c)
    save_jar(path, jar)


def header_for(jar, host: str) -> str:
    """按域名匹配生成 Cookie 请求头。"""
    hostname = (host or "").split(":")[0]
    pairs = []
    for c in jar:
        d = (c.get("domain") or "").lstrip(".")
        if not d or not c.get("name"):
            continue
        if hostname == d or hostname.endswith("." + d):
            pairs.append(f"{c['name']}={c.get('value', '')}")
    return "; ".join(pairs)
