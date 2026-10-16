"""可选功能：用本机 Ollama 把自然语言转成 HTTP 请求（零第三方依赖，无 Ollama 时优雅降级）。"""

import json
import urllib.error
import urllib.request

from .errors import AiUnavailable

DEFAULT_MODEL = "qwen2.5:latest"
OLLAMA_URL = "http://localhost:11434"

_SYSTEM = (
    "You are an HTTP request generator. Given a user description, output a single "
    "JSON object with fields: method (uppercase HTTP verb), url (string), "
    "headers (object), body (object or null). Output ONLY the JSON, no explanation."
)


def generate_request(prompt: str, model=DEFAULT_MODEL, base_url=OLLAMA_URL) -> dict:
    url = base_url.rstrip("/") + "/api/generate"
    payload = {
        "model": model,
        "system": _SYSTEM,
        "prompt": prompt,
        "format": "json",
        "stream": False,
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            out = json.loads(resp.read())
    except urllib.error.URLError as e:
        raise AiUnavailable(
            f"无法连接本地 Ollama（{base_url}）：{e.reason}。\n"
            f"请先安装 Ollama 并运行 `ollama serve`，再 `ollama pull {model}`，"
            f"或加 --url 指向其它 OpenAI 兼容端点。"
        )
    text = out.get("response", "")
    try:
        return json.loads(text)
    except Exception:
        raise AiUnavailable("Ollama 返回了无法解析的内容，请重试或换模型。")
