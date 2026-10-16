# Changelog

本项目遵循语义化版本。所有版本均为**零第三方依赖**。

## [Unreleased] — 待发布
仅文档与路线图更新。

## [0.1.0] — 首个版本

### 核心
- 方法即命令：`httpeek get/post/put/delete/patch/head/options <url>`，彩色美化输出。
- 请求选项：`-H` `-d` `-q` `--bearer` `-t` `-o` `--json` `--insecure` `--no-color`。
- `run <file>` 按顺序执行集合请求；`mock <file>` 把集合变成本地 Mock 服务。
- `init` 生成示例集合；`ai "<描述>" [--run]` 用本机 Ollama 生成请求（可选，优雅降级）。

### 对标同类工具的增强
- **输出体验（对标 HTTPie）**：类型感知彩色 JSON；`-v/--verbose`、`--only-headers`、
  `--only-body`、`--quiet`；`-r/--repeat N` 与平均/最快/最慢耗时统计。
- **集合能力（对标 Bruno/Hoppscotch）**：`${ENV}` 环境变量展开（缺失即报错）；
  `expect` 断言 + `run --strict` 非零退出码。
- **Mock 能力（对标 Mockoon/Prism）**：路径参数 `/users/{id}`；响应模板
  `{{request.method/path/query.KEY/body.KEY/params.id}}`；查询规则匹配；`delay` 毫秒延迟模拟。

### 工程
- 32 个单元测试（标准库 unittest，不依赖网络）。
- CI：Python 3.8–3.13 矩阵。
- MIT 许可证，纯 Python 标准库实现，支持 `python -m httpeek` 免安装运行。
