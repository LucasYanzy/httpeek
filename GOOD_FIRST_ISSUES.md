# Good First Issues（持续维护）

> 这些 Issue 用于引导新贡献者上手。所有改动都必须**只使用 Python 标准库**
> （httpeek 的零依赖铁律）。可参考 `CONTRIBUTING.md`。
>
> **已实现、勿重复认领**：`${ENV}` 展开、`expect` 断言、`--repeat` 统计、
> 彩色/可配置输出、Mock 路径参数与模板、`--save`、`import "curl ..."`、`-F` 表单上传、
> `history` 请求历史（记录 + 回放）。
> 这些已在 v0.1.0 / v0.2.0 及后续版本中完成（对应 issue 已关闭）。

---

## 1. [Feature] 请求历史 `httpeek history`（记录 + 回放）——✅ 已实现

**背景**：终端里刚发过的请求想再跑一次，只能翻 shell 历史；希望 httpeek 自己记住。

**验收**：
- 每次请求后把 method/url/headers/body 追加到本地 `~/.httpeek/history.jsonl`（可用环境变量 `HTTPEEK_HOME` 覆盖）。
- `httpeek history` 列出最近 N 条（带序号与时间）；`httpeek history 3` 重放第 3 条。
- 加 `--no-history` 或配置项可关闭；默认开启但绝不上传任何数据。

**实现**：新增 `httpeek/history.py`，`cli.py` 增加 `history` 子命令与 `--no-history`；
测试见 `tests/test_history.py`。

---

## 2. [Feature] `--to-curl` 把请求导出成 curl 命令（与 `import` 对称）

**背景**：`import` 能把 curl 转进来，反过来也应该能把集合条目/当前请求导出成 curl，
方便贴给别人或写进文档。

**验收**：
- `httpeek get <url> -H 'X-T: 1' --to-curl` 打印等价的 curl 命令（不发送，或加 `--dry-run`）。
- `httpeek run c.json --to-curl` 为每条请求打印一条 curl。
- multipart / JSON body / bearer 都要正确转义（注意 shell 引号）。

**提示**：新增 `exporter.py`，实现 `to_curl(method, url, headers, body)`；
字符串用 `shlex.quote` 转义。

**标签**：`good first issue`, `enhancement`

---

## 3. [Feature] Cookie / 会话保持

**背景**：登录类接口需要先拿 cookie 再访问，目前每次请求互相独立。

**验收**：
- `httpeek post <login-url> -d ... --save-cookies jar.json` 把响应 `Set-Cookie` 存入文件。
- 后续请求加 `--cookies jar.json` 自动带上，并持续更新。
- 集合里可写 `"cookies": "jar.json"` 对整个集合生效。

**提示**：用标准库 `http.cookiejar.MozillaCookieJar` 做存取最省事。

**标签**：`good first issue`, `enhancement`

---

## 4. [Feature] 从 OpenAPI 自动生成 mocks

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

## 5. [Docs/Chore] 录制终端演示动图 + 更新 README 演示区

**背景**：README 的演示目前是静态文本。调研表明"清晰 demo"对 star 增长帮助最大。

**验收**：
- 在 `demo/` 下补充一键脚本（已有 `demo/install_to_result.sh` 可参考）。
- 若环境有 `asciinema`，附录制命令并用 `agg` 转 GIF。
- 在 README「演示」一节嵌入动图，并注明如何本地复现。

**提示**：`demo/demo.py` 已给出基础框架（含路径参数与模板演示）。

**标签**：`good first issue`, `documentation`
