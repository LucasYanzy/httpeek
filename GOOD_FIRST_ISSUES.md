# Good First Issues（发布前预建 5 个）

> 这些 Issue 在首次发布时一并创建，方便新贡献者快速上手。
> 所有改动都必须**只使用 Python 标准库**（httpeek 的零依赖铁律）。
> 可参考 `CONTRIBUTING.md`。
>
> 注意：以下 5 个均为**尚未实现**的功能；`${ENV}` 展开、`expect` 断言、`--repeat`
> 统计等已在 v0.1.0 中完成，不再作为 issue 发布。

---

## 1. [Feature] 加 `--save <file>` 把一次请求追加进集合

**背景**：现在只能手动编辑 JSON 集合。希望发送请求时能顺手存成集合条目。

**验收**：
- `httpeek get https://x.com/a --save my.json` 在文件不存在时创建、存在时追加一条 `requests`。
- 保存的条目含 `method/path/headers/body/query`。
- `httpeek run my.json` 能正常执行它。

**提示**：在 `cli.py` 的 method 分支里，发送成功后把请求结构写入 JSON；复用
`collection.load_collection` 的思路。注意合并时保留已有 `requests` 与 `mocks`。

**标签**：`good first issue`, `enhancement`

---

## 2. [Feature] 支持 `-F/--form` multipart 表单与文件上传

**背景**：当前 `-d` 只能发 JSON 或纯文本，无法模拟表单提交/文件上传。

**验收**：
- `httpeek post <url> -F "name=httpeek" -F "file=@./a.txt"` 能正确构造 `multipart/form-data`。
- 服务端能解析到字段与文件内容。
- 在帮助文本与 README 里补一行说明。

**提示**：用 `uuid` 生成 boundary，手工拼装 multipart 正文（纯标准库即可），
并设置正确的 `Content-Type: multipart/form-data; boundary=...`。

**标签**：`good first issue`, `enhancement`

---

## 3. [Feature] `httpeek import "curl ..."` 从 curl 命令导入

**背景**：很多人手上已有大量 curl 命令，希望一键转成 httpeek 集合条目。

**验收**：
- `httpeek import "curl -X POST https://x.com/a -H 'X-T: 1' -d '{\"a\":1}'" [--save c.json]`
- 解析出 method / url / headers / body / query，打印解析结果，可选写入集合。
- 遇到不支持的 curl 参数（如 `--compressed`）给出清晰提示而非崩溃。

**提示**：用 `shlex.split` 解析命令行，然后逐参数映射；放在新文件 `importer.py`。

**标签**：`good first issue`, `enhancement`

---

## 4. [Feature] 从 OpenAPI 自动生成 mocks

**背景**：手写 `mocks` 繁琐；已有 OpenAPI/Swagger 文档的项目应能直接生成。

**验收**：
- `httpeek mock --from-openapi spec.json --port 8080` 读取 `paths` 与 `responses`，
  为每个 `path` + `method` 生成一条 mock（用文档里的 `example` 或按 schema 生成占位值）。
- 生成的路由可直接被 `httpeek get` 命中。
- 在 README「集合文件格式」里补充一小节。

**提示**：OpenAPI 多为 JSON（少数 YAML 需说明不支持）；从 `paths[path][method].responses[code].content`
提取示例。放在新文件 `openapi.py`。

**标签**：`good first issue`, `enhancement`

---

## 5. [Docs/Chore] 录制终端演示动图 + 更新 README 演示区

**背景**：README 的演示目前是静态文本。调研表明"清晰 demo"对 star 增长帮助最大。
希望有可复现的录制脚本与动图。

**验收**：
- 在 `demo/` 下补充一键脚本：自动启动 mock、发请求、退出，输出与 README 一致。
- 若环境有 `asciinema`，附一条录制命令（`asciinema rec demo.cast`），并用 `agg` 转 GIF。
- 在 README「演示」一节嵌入动图，并注明如何本地复现。

**提示**：`demo/demo.py` 已给出基础框架（含路径参数与模板演示），可扩展让
mock 端口可参数化；也可直接用 `httpeek init` + `httpeek mock` 录制真实流程。

**标签**：`good first issue`, `documentation`
