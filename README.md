# httpeek

> 终端里的 HTTP 客户端 + 内置 Mock 服务。**零第三方依赖、零账号、可离线。**

`httpeek` 让你用一条命令发送 HTTP 请求并漂亮地打印结果；更特别的是，同一份集合文件既能**发送**请求，也能一键变成一个**本地 Mock 服务**。没有云、没有账号、没有 `npm install`——连 Python 第三方包都不需要。

```bash
# 免安装直接跑（需要 Python 3.8+，系统自带即可）
python -m httpeek get https://api.github.com/zen

# 或装成全局命令（依然零依赖）
pipx install httpeek        # 或：pip install httpeek / uvx httpeek
httpeek get https://api.github.com/zen
```

---

## ✨ 演示

```
$ httpeek get https://api.github.com/zen
→ 200 OK (312 ms) https://api.github.com/zen
  Content-Type: text/plain;charset=utf-8
  Content-Length: 19

  Accessible for all.

# 离线 Mock：一份文件既是请求集，也是 Mock 服务
$ httpeek init demo.json && httpeek mock demo.json
httpeek mock 已启动： http://127.0.0.1:8080
$ httpeek get http://127.0.0.1:8080/hello
→ 200 OK (0 ms) http://127.0.0.1:8080/hello
  {"message": "你好，这是 httpeek 的本地 Mock 响应", "ok": true}
```

想看完整离线演示？`python demo/demo.py`（不依赖网络）。

---

## 🚀 为什么是 httpeek

| 能力 | httpeek | HTTPie | Postman | curl |
|------|---------|--------|---------|------|
| 一条命令、零配置 | ✅ | ⚠️ 需装 | ❌ 需账号 | ✅ 但不美观 |
| 零第三方依赖 / 免 `pip install` | ✅ | ❌ | ❌ | ✅ |
| 持久化请求集合（纯文件、可 Git） | ✅ | ⚠️ | ✅ | ❌ |
| **同一文件 = 本地 Mock 服务** | ✅ | ❌ | ⚠️ | ❌ |
| 离线可用 | ✅ | ✅ | ❌ | ✅ |
| 可选本地 AI 生成请求（Ollama） | ✅ | ❌ | ❌ | ❌ |

---

## 📦 安装

任选其一，都**不需要任何第三方依赖**：

```bash
python -m httpeek            # 方式一：免安装，直接用（推荐先试试）
pipx install httpeek         # 方式二：装成全局命令（隔离环境）
pip install httpeek          # 方式三：普通安装
uvx httpeek                  # 方式四：一次性运行（uv 用户）
```

---

## 🛠 用法

### 发送一次请求（方法即命令）

```bash
httpeek get  https://api.github.com/repos/octocat/Hello-World
httpeek post https://httpbin.org/post -d '{"name":"httpeek"}' -H "X-Token: 1"
httpeek get  https://httpbin.org/get -q "q=python" -q "page=1" --bearer "$TOKEN"
httpeek delete https://httpbin.org/delete --insecure

# 更细的输出控制（对标 HTTPie 的 --print）
httpeek get https://api.github.com/zen -v --only-body   # 只看响应体 + 打印请求
httpeek get https://httpbin.org/get -r 5               # 重复 5 次，打印耗时统计
```

常用选项：`-H/--header K:V`、`-d/--data JSON或文本`、`-q/--query k=v`、`--bearer`、
`-t/--timeout 秒`、`-o/--output 文件`、`--json`（管道友好）、`--insecure`、`--no-color`、
`-v/--verbose`（打印请求行/请求头）、`--only-headers`、`--only-body`、`--quiet`、`-r/--repeat N`。

### 运行请求集合

```bash
httpeek init demo.json       # 生成示例集合
httpeek run  demo.json       # 按顺序发送里面的请求
```

### 把集合变成本地 Mock 服务

```bash
httpeek mock demo.json --port 8080
# 另开终端：httpeek get http://127.0.0.1:8080/hello
```

### 用自然语言生成请求（可选，需本机 Ollama）

```bash
httpeek ai "获取北京今天的天气" --model qwen2.5:latest --run
```

没有 Ollama 时会友好提示，不影响其它功能。

---

## 📄 集合文件格式（JSON，纯文本、可 Git）

```json
{
  "name": "我的 API",
  "base_url": "https://api.example.com",
  "headers": { "Accept": "application/json" },
  "requests": [
    { "name": "列表", "method": "GET",  "path": "/users", "query": { "page": "1" } },
    { "name": "创建", "method": "POST", "path": "/users", "body": { "name": "httpeek" } },
    { "name": "健康", "method": "GET", "path": "/health",
      "expect": { "status": 200, "contains": "ok" } }
  ],
  "mocks": [
    { "method": "GET", "path": "/users", "status": 200,
      "headers": { "Content-Type": "application/json" },
      "body": { "users": [] } },
    { "method": "GET", "path": "/users/{id}", "status": 200,
      "body": { "id": "{{request.params.id}}", "q": "{{request.query.v}}" } }
  ]
}
```

- `requests[].body` 若是对象/数组会自动序列化为 JSON 并设置 `Content-Type`。
- `mocks[]` 会被 `mock` 子命令当作路由；未匹配的请求返回 `404`。

**集合里的高级特性：**
- **环境变量**：`base_url` / `headers` / `body` 中写 `${TOKEN}`，运行时替换为 `os.environ["TOKEN"]`；缺失则明确报错（便于保密信息不入仓库）。
- **断言（`expect`）**：请求条目可加 `"expect": {"status": 200, "contains": "ok"}`，`run` 时自动校验；配合 `httpeek run x.json --strict` 可做轻量契约/冒烟测试，失败返回非零退出码。
- **路径参数**：mock 路由写成 `"/users/{id}"`，会匹配 `/users/42`，并在响应模板里用 `{{request.params.id}}` 取到 `42`。
- **响应模板**：mock 的 `body`/`headers` 支持 `{{request.method}}`、`{{request.path}}`、`{{request.query.KEY}}`、`{{request.body.KEY}}`、`{{request.params.id}}`。
- **查询规则**：mock 里写 `"query": {"v":"1"}` 时，仅当请求查询匹配才路由，否则 404。
- **延迟模拟**：mock 里写 `"delay": 300` 表示响应前等待 300 毫秒，模拟真实网络。

---

## ❓ 常见问题（FAQ）

**Q：一定要安装吗？** 不用。`python -m httpeek` 即可，只需要系统自带的 Python 3.8+。

**Q：它和 curl/HTTPie 有什么区别？** curl 不美观、无集合；HTTPie 需安装且不能当 Mock。httpeek 把「发送 + 集合 + 本地 Mock」合一，且零第三方依赖。

**Q：Mock 模式安全吗？** 它只监听你指定的 `host:port`（默认 `127.0.0.1:8080`），不联网、不上传任何数据。

**Q：支持 HTTPS 吗？** 支持。自签名证书可用 `--insecure` 跳过校验。

**Q：AI 功能要付费吗？** 不。它只调用**本机**的 Ollama（`localhost:11434`）。没有 Ollama 时该命令会提示，不报错中断。

---

## 🗺 路线图

**已完成 ✅**
- [x] `${ENV}` 环境变量占位符
- [x] `expect` 断言 + `run --strict`（轻量契约测试）
- [x] 彩色、可配置输出（`-v` / `--only-headers` / `--only-body` / `--quiet`）
- [x] `--repeat N` 与耗时统计
- [x] Mock 路径参数 / 响应模板 / 查询规则 / 延迟模拟

**待做 🚧**
- [ ] 从 OpenAPI 自动生成 `mocks`
- [ ] `--save` 把请求存回集合、`-F` 表单上传、`import` 从 curl 导入
- [ ] 响应差异对比（diff）与请求历史记录
- [ ] 终端演示动图（见 good first issue）

欢迎在 Issue 里提建议，或认领 **good first issue**。

---

## 🤝 贡献

详见 [CONTRIBUTING.md](CONTRIBUTING.md)。**铁律：只使用 Python 标准库，不引入第三方依赖。**

## 📄 许可证

[MIT](LICENSE) —— 随便用、随便改。
