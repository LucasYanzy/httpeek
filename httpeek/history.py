"""请求历史记录：本地 JSONL 文件，纯标准库，数据只留在本机。

历史文件默认位于 ``~/.httpeek/history.jsonl``，每行一条 JSON。
可用环境变量 ``HTTPEEK_HOME`` 改变目录。任何写入/读取都绝不会联网。
"""

import json
import os
import time

from .errors import HttpPeekError

#: 默认展示的条目数（`httpeek history` 不带 -n 时）。
DEFAULT_LIMIT = 20

#: 历史文件名（位于 HTTPEEK_HOME 目录下）。
FILENAME = "history.jsonl"


def history_dir():
    """历史目录：``HTTPEEK_HOME`` 优先，否则 ``~/.httpeek``。"""
    home = os.environ.get("HTTPEEK_HOME")
    if home:
        return os.path.abspath(os.path.expanduser(home))
    return os.path.join(os.path.expanduser("~"), ".httpeek")


def history_path():
    """历史文件的完整路径。"""
    return os.path.join(history_dir(), FILENAME)


def _ensure_parent(path):
    """确保目标文件的父目录存在（不存在则创建）。"""
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)


def _jsonable_body(body):
    """只保存可 JSON 序列化的 body（dict/list/str）；其余（如 multipart 字节）记为 None。"""
    if isinstance(body, (dict, list, str)):
        return body
    return None


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


def record(method, url, headers=None, body=None, path=None, timestamp=None):
    """把一次请求追加到历史文件（每行一个 JSON），返回写入的条目。

    目录/文件不存在会自动创建。写入是「尽力而为」的：即使磁盘不可写也不会
    让调用方的请求失败（异常被吞掉，只是这一条历史没记上）。
    """
    entry = {
        "timestamp": timestamp or _now(),
        "method": (method or "GET").upper(),
        "url": url or "",
        "headers": dict(headers or {}),
        "body": _jsonable_body(body),
    }
    target = path or history_path()
    try:
        _ensure_parent(target)
        line = json.dumps(entry, ensure_ascii=False)
        with open(target, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        # 历史只是附加价值，绝不因为它而让真正的请求失败。
        return entry
    return entry


def load_entries(path=None):
    """读取全部历史条目。

    - 文件/目录不存在 → 返回空列表（不报错）。
    - 某行不是合法 JSON（文件被破坏）→ 跳过该行，继续读后面的。
    - 文件不可读 → 返回已读到的部分。
    """
    target = path or history_path()
    entries = []
    if not os.path.exists(target):
        return entries
    try:
        with open(target, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except (ValueError, TypeError):
                    continue  # 坏行：安静跳过，不崩溃
                if isinstance(obj, dict):
                    entries.append(obj)
    except OSError:
        return entries
    return entries


def recent(limit=DEFAULT_LIMIT, path=None):
    """返回最近 ``limit`` 条，元素为 ``(序号, 条目)``；序号从 1 开始，跨整个文件。"""
    entries = load_entries(path)
    try:
        n = int(limit)
    except (TypeError, ValueError):
        n = DEFAULT_LIMIT
    if n <= 0:
        return []
    start = max(0, len(entries) - n)
    return [(i + 1, e) for i, e in enumerate(entries[start:], start=start)]


def get_entry(number, path=None):
    """按 1 起始的序号取一条历史条目；越界或非整数则抛出 HttpPeekError。"""
    entries = load_entries(path)
    try:
        n = int(number)
    except (TypeError, ValueError):
        raise HttpPeekError(f"历史编号需要是整数，收到：{number!r}")
    if n < 1 or n > len(entries):
        raise HttpPeekError(
            f"历史里没有编号 {n} 的请求（当前共 {len(entries)} 条）。"
        )
    return entries[n - 1]


def entry_to_request(entry):
    """把一条历史条目转成 ``send_request`` 需要的关键字参数。"""
    return {
        "method": entry.get("method") or "GET",
        "url": entry.get("url") or "",
        "headers": entry.get("headers") or {},
        "body": entry.get("body"),
    }
