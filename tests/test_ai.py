"""ai 模块的测试：无 Ollama 时应优雅报错。"""

import unittest

from httpeek.ai import generate_request, AiUnavailable


class TestAi(unittest.TestCase):
    def test_unavailable_raises(self):
        # 连接一个几乎必然拒绝的端口，验证优雅降级
        with self.assertRaises(AiUnavailable):
            generate_request("ping", base_url="http://127.0.0.1:1")

    def test_defaults(self):
        from httpeek.ai import DEFAULT_MODEL, OLLAMA_URL
        self.assertTrue(DEFAULT_MODEL)
        self.assertTrue(OLLAMA_URL.startswith("http"))


if __name__ == "__main__":
    unittest.main()
