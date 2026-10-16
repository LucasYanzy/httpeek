#!/usr/bin/env bash
# httpeek：从「零安装」到「跑出结果」的完整演示（可复现、完全离线）
set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
cd "$TMP_DIR"

echo "\$ python3 -m venv .venv"
python3 -m venv .venv >/dev/null

echo "\$ .venv/bin/pip install httpeek        # 真实安装（零依赖）"
.venv/bin/pip install --quiet "$REPO_ROOT"
echo

echo "\$ httpeek version"
.venv/bin/httpeek version
echo

echo "\$ httpeek init demo.json                # 生成示例集合"
.venv/bin/httpeek init demo.json
echo

echo "\$ httpeek mock demo.json --port 8099 &  # 把同一份文件变成 Mock 服务"
.venv/bin/httpeek mock demo.json --port 8099 >/dev/null 2>&1 &
MOCK_PID=$!
sleep 2

echo "\$ httpeek get http://127.0.0.1:8099/hello"
.venv/bin/httpeek get http://127.0.0.1:8099/hello
echo

echo "\$ httpeek get http://127.0.0.1:8099/users/42?v=9   # 路径参数 + 响应模板"
.venv/bin/httpeek get http://127.0.0.1:8099/users/42?v=9
echo

kill "$MOCK_PID" 2>/dev/null || true
wait "$MOCK_PID" 2>/dev/null || true
echo "✓ 演示完成（mock 已停止）"

cd / && rm -rf "$TMP_DIR"
