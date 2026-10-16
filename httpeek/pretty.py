"""终端美化输出：按需上色，管道/NO_COLOR 时自动关闭。"""

import json
import os
import re
import sys


def _color_on() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


def _c(code: int, text: str) -> str:
    if not _color_on():
        return text
    return f"\033[{code}m{text}\033[0m"


def bold(t):       return _c(1, t)
def dim(t):        return _c(2, t)
def red(t):        return _c(31, t)
def green(t):      return _c(32, t)
def yellow(t):     return _c(33, t)
def blue(t):       return _c(34, t)
def magenta(t):    return _c(35, t)
def cyan(t):       return _c(36, t)
def gray(t):       return _c(90, t)


def status_color(code: int) -> str:
    if code < 300:
        return green(str(code))
    if code < 400:
        return cyan(str(code))
    if code < 500:
        return yellow(str(code))
    return red(str(code))


def render_json(obj, indent: int = 0) -> str:
    """类型感知的彩色 JSON 渲染（对标 HTTPie 的语法高亮）。"""
    pad = "  " * indent
    pad1 = "  " * (indent + 1)
    if isinstance(obj, dict):
        if not obj:
            return "{}"
        items = [
            f"{pad1}{cyan(json.dumps(k, ensure_ascii=False))}: {render_json(v, indent + 1)}"
            for k, v in obj.items()
        ]
        return "{\n" + ",\n".join(items) + "\n" + pad + "}"
    if isinstance(obj, list):
        if not obj:
            return "[]"
        items = [f"{pad1}{render_json(v, indent + 1)}" for v in obj]
        return "[\n" + ",\n".join(items) + "\n" + pad + "]"
    if isinstance(obj, str):
        return green(json.dumps(obj, ensure_ascii=False))
    if isinstance(obj, bool):
        return magenta("true" if obj else "false")
    if obj is None:
        return magenta("null")
    if isinstance(obj, (int, float)):
        return yellow(str(obj))
    return dim(str(obj))


def format_body(body, content_type: str = "") -> str:
    """把响应体渲染成可读文本；JSON 自动美化并按类型上色（终端下）。"""
    if isinstance(body, (bytes, bytearray)):
        text = body.decode("utf-8", errors="replace")
    else:
        text = str(body)
    ct = (content_type or "").lower()
    if "json" in ct:
        try:
            obj = json.loads(text)
        except Exception:
            return text
        if _color_on():
            return render_json(obj)
        return json.dumps(obj, indent=2, ensure_ascii=False)
    return text
