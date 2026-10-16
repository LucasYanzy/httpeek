# 贡献指南（CONTRIBUTING）

感谢你来贡献 **httpeek**！这是一个坚持"零第三方依赖"的小工具，目标是一个人也能轻松维护。

## 本地开发

```bash
git clone https://github.com/httpeek/httpeek
cd httpeek
# 免安装直接跑：
python -m httpeek version
python -m httpeek get https://api.github.com/zen
```

无需 `pip install`、无需虚拟环境、无需联网（mock 模式完全离线）。

## 运行测试

```bash
python -m unittest discover -s tests -v
```

测试全部基于标准库 + 本地临时 HTTP 服务，**不依赖网络**，可在任意干净环境复现。

## 核心约束（很重要）

- **只使用 Python 标准库。** 这是为了"零配置一条命令能跑"的承诺。新增功能若必须引入依赖，请先在 Issue 里讨论。
- 代码风格：跟随 PEP 8，保持简洁；用 `python -m py_compile` 自检语法。
- 提交信息：推荐 Conventional Commits（`feat:` / `fix:` / `docs:` / `chore:`）。

## 提交流程

1. Fork 并新建分支（`git checkout -b fix/xxx`）。
2. 改动 + 测试 + 文档。
3. 提 PR，勾选 PR 模板清单，关联 Issue。

## 想认领任务？

看仓库的 **good first issue** 标签，或者直接开 Issue 讨论你的想法。我们尤其欢迎：
- 新的输出格式（如 `--json` 增强）
- 集合格式的易用性改进
- 文档与示例

期待你的 PR！
