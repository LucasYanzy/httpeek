"""httpeek 自定义异常。"""


class HttpPeekError(Exception):
    """httpeek 的基础错误。"""


class AiUnavailable(HttpPeekError):
    """本地 Ollama 不可用或返回无法解析的内容。"""
