# Good First Issues（持续维护）

> 这些 Issue 用于引导新贡献者上手。所有改动都必须**只使用 Python 标准库**
> （httpeek 的零依赖铁律）。可参考 `CONTRIBUTING.md`。
>
> **已实现、勿重复认领**：`${ENV}` 展开、`expect` 断言、`--repeat` 统计、
> 彩色/可配置输出、Mock 路径参数与模板/查询规则/延迟、`--save`、
> `import "curl ..."`、`-F` 表单上传、`--to-curl` 导出、`httpeek history`、Cookie 会话。
> 这些已分别合入 v0.1.0 / v0.2.0 / v0.3.0（对应 issue 已关闭）。

---

## 1. [Feature] 从 OpenAPI 自动生成 mocks

**背景**：手写 `mocks` 繁琐；已有 OpenAPI/Swagger 文档的项目应能直接生成。

**验收**：
- `httpeek mock --from-openapi spec.json --port 8080` 读取 `paths` 与 `responses`，
  为每个 path + method 生成一条 mock（用文档里的 example 或按 schema 生成占位值）。
- 生成的路由可直接被 `httpeek get` 命中。
- 在 README「集合文件格式」里补充一小节。

**提示**：从 `paths[path][method].responses[code].content` 提取示例；放在新文件 `openapi.py`。
（少数 YAML 文档需说明暂不支持。）

**标签**：`good first issue`, `enhancement`

---

## 2. [Feature] 响应差异对比（diff）

**背景**：接口改版 / 前后端联调时，常想知道两次响应差在哪里。

**验收**：
- `httpeek get <url> -r 2 --diff` 发送两次，若响应体不同则打印差异（JSON 按 key 对比更好）。
- 支持 `--diff <file.json>`：与本地快照文件对比。
- 有差异时退出码非零（便于 CI）。

**提示**：标准库 `difflib.unified_diff` 可做文本 diff；JSON 可递归比较后输出结构化差异。
注意仍要保持零依赖。

**标签**：`good first issue`, `enhancement`

---

## 3. [Feature] 集合多环境（profiles）

**背景**：同一套请求在 dev / staging / prod 下 base_url 与密钥不同，现在要维护多个文件。

**验收**：
- 集合支持 `"profiles": {"dev": {"base_url": "...", "headers": {...}}}`。
- `httpeek run c.json --profile dev` 使用对应覆盖项；不指定则用顶层默认。
- `mock` 同样支持 `--profile`；在 README 补充示例。

**提示**：在 `collection.py` 里加载后做一次「深合并」即可，注意 `${ENV}` 的展开时机。

**标签**：`good first issue`, `enhancement`

---

## 4. [Feature] `httpeek docs <file>` 从集合生成 Markdown 文档

**背景**：集合里已经有请求与 Mock，应该能一键导出成可读的接口文档。

**验收**：
- `httpeek docs c.json -o API.md` 生成 Markdown：按请求列出 method / path /
  headers / query / body 示例，以及 mock 路由与示例响应。
- 输出到 stdout 或 `-o` 指定文件。
- 在 README 里补一小节说明。

**提示**：纯字符串拼装 + f-string 即可；注意代码块要正确闭合。

**标签**：`good first issue`, `enhancement`

---

## 5. [Docs/Chore] 录制终端演示动图 + 更新 README 演示区

**背景**：README 的演示目前是静态文本。调研表明"清晰 demo"对 star 增长帮助最大。

**验收**：
- 在 `demo/` 下补充一键脚本（已有 `demo/install_to_result.sh` 可参考）。
- 若环境有 `asciinema`，附录制命令并用 `agg` 转 GIF。
- 在 README「演示」一节嵌入动图，并注明如何本地复现。

**提示**：`demo/demo.py` 已给出基础框架（含路径参数与模板演示）。

**标签**：`good first issue`, `documentation`
