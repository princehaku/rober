# PRD - O5 Public Health Tunnel External Evidence

## 1. 产品问题

O5 当前约 `85%`，真实公网入口仍缺 success-class external evidence。现有 relay 同时承载健康、状态、archive 和 command POST API；把 Cloudflare quick tunnel 直接指向 relay 会扩大写入与命令面，不能为获取 `/healthz` 证据而接受该风险。

本 sprint 需要建立一个最小且可证明的公网健康通道：外部只能访问 `GET/HEAD /healthz`，其他入口在到达 relay 之前全部 fail closed，然后从开发机完成一次真实 certificate-valid HTTPS capture。

## 2. 用户旅程与触点收益

目标用户是需要判断上位机 cloud relay 是否在线的工程/运维人员：

1. Engineer 在上位机启动 helper-owned relay、allowlist proxy 和 temporary cloudflared。
2. 开发机从公网执行 `GET /healthz` 与 `HEAD /healthz`，获得 `2xx/3xx` 和有效 TLS/certificate 证据。
3. 开发机对 command、archive、status、query 和编码绕过执行负向矩阵，确认只读健康面之外全部 `404/405`。
4. capture 输出脱敏 artifact；支持人员只看到 host hash、TLS/cert 摘要、HTTP class、bucket timing、provider/version 和 negative matrix，看不到 raw URL、token、header 或 body。
5. helper 结束后 relay、proxy、cloudflared 和临时文件全部退出，cleanup residual=`0`。

用户收益是「能验证在线，但不能误触控制」；本轮不增加用户任务操作能力，不把临时 tunnel 伪装成生产云。

## 3. 范围与需求

### 3.1 Health-only proxy

- 使用 Python 标准库实现，不新增第三方运行依赖。
- proxy 与 relay host publish 都固定在 `127.0.0.1`。
- 仅精确允许：
  - `GET /healthz`
  - `HEAD /healthz`
- `HEAD` 必须返回与健康探测一致的安全状态和 headers，但 body 长度为零；不得把 relay 不支持的 HEAD 直接暴露为公网能力。
- 其他 path 或带 query 的 target 返回 `404`。
- 精确 `/healthz` 的 POST/PUT/PATCH/DELETE/OPTIONS 等返回 `405`。
- 百分号编码、双斜杠、反斜杠、点段、absolute-form URI、fragment-like 输入和超长 target 全部 fail closed。
- 不将外部 Authorization、Cookie、Host、forwarded header 或 body 转发给 upstream。
- upstream 固定为 loopback relay 的 `/healthz`，不能由请求参数改写。

### 3.2 官方 cloudflared provenance

- 上位机已确认 `aarch64`，选择 Cloudflare 官方 ARM64 Linux release asset。
- 只允许访问 Cloudflare 官方 release/API 的 HTTPS 地址。
- 从官方 API 在当前 run 动态读取 release version、asset URL 和 SHA256 digest；不得把未知 checksum 写死到代码或文档。
- 下载后计算本地 SHA256，与官方 digest 精确比对；digest 缺失、格式错误或 mismatch 均停止。
- 执行 `cloudflared --version`，必须与官方 release version/ARM64 asset 匹配。
- runtime 只落在 helper-owned 临时目录；不安装、不升级系统、不持久化。

### 3.3 一次 live capture

- capture helper 为 relay、proxy、cloudflared 建立唯一 run id、PID/process-group ownership 和 trap/finally cleanup。
- tunnel target 必须是 `http://127.0.0.1:<proxy_port>`，禁止使用 relay port。
- raw tunnel URL 只能存在于运行时内存/临时受控流；不得进入 artifact、`tech-done.md` 或 git diff。
- 开发机用默认信任链验证 HTTPS certificate，不允许 `-k`、禁用 hostname 校验或降级 HTTP。
- `GET/HEAD /healthz` 必须获得 certificate-valid HTTPS `2xx/3xx`。
- 公网负向矩阵必须覆盖 `/readyz`、`/preflightz`、`/api/status`、`/api/commands/collect`、`/api/o6/archive/tasks`、query、encoded path、double slash、absolute-form 和 `/healthz` 非允许 method；结果必须是 proxy 的 `404/405`，不能触达 relay handler。
- capture 前后 relay state checksum 必须相同；artifact 只记录 `state_unchanged=true/false`，不记录 state 内容或本机路径。
- 结束后上位机 relay/proxy/cloudflared/helper-owned 临时目录 residual 必须为 `0`。

### 3.4 Artifact 最小化

primary artifact 只允许保存：

- public host 的单向 SHA256 hash，不保存 raw URL/hostname；
- TLS protocol、certificate validity/issuer/fingerprint 等安全摘要；
- HTTP status class，不保存 response body；
- 粗粒度 bucket timing，不保存可回推的高精度 trace；
- provider=`cloudflare`、官方 release version、asset architecture 和 SHA256 verification boolean；
- negative matrix，包括 path/method/query/encoding 隔离、state unchanged 和 cleanup residual 结论。

artifact 禁止保存 raw URL、token、Authorization、Cookie、headers、request/response body、relay state、完整 certificate、tunnel log 或本地/远端绝对路径。

## 4. 验收口径

| Gate | 必须满足 | 失败结果 |
| --- | --- | --- |
| 本地实现 | 标准库 proxy；relay/proxy 仅 `127.0.0.1` | flat，禁止 live |
| allowlist | 只有精确 GET/HEAD `/healthz` 可通过 | flat，安全缺陷必须先修 |
| 负向隔离 | 其他 path/query/编码为 `404`；其他 method 为 `405` | flat |
| runtime provenance | 官方 HTTPS API/release、aarch64 ARM64、version 与 SHA256 全部验证 | flat，不执行 binary |
| public HTTPS | 开发机默认 trust store 验证 TLS/cert，GET/HEAD 为 `2xx/3xx` | flat |
| 无副作用 | 前后 state checksum 不变 | flat |
| redaction | artifact 无 raw URL/token/header/body/path | flat |
| cleanup | helper-owned relay/proxy/cloudflared residual=`0` | flat |

禁止所有 command/task/manual/`cmd_vel`/UART/route/delivery/HIL。负向请求只能命中 proxy 拒绝逻辑，不得为了验证而真正下发命令或写 archive。

## 5. OKR 映射与方向判断

- Objective：O5，当前最低约 `85%`。
- 核心抓手：真实公网 certificate-valid HTTPS health-only evidence，而不是新的本地包装层。
- 方向：`继续 O5，一次性执行外部证据抓手`。
- 全 gate 通过：`current_run_artifact_delta=true`、`external_artifact_delta=true`，O5 `85% -> 86%`。
- 任一 gate 失败：O5 保持 `85%`，记录 blocker，不以 readback/export/preview 再包装。
- 无论成功与否：`production_ready=false`、`mission_objective_0_satisfied=false`、KR `不归档`。

temporary tunnel 不证明稳定 DNS、生产凭证、4G、production DB/queue、worker、OSS/CDN、真手机、route、delivery 或 HIL。

## 6. Owner、依赖与风险

- Delivery owner：`full-stack-software-engineer`。
- Product acceptance：`product-okr-owner`。
- 依赖：上位机 SSH、Cloudflare 官方 API/release、Cloudflare edge、开发机公网与系统 trust store。
- 主要风险：official digest 缺失、provider 网络不可达、quick tunnel URL 获取超时、edge 重定向异常、cleanup 失败或负向矩阵发现穿透。
- 失败恢复：立即清理 helper-owned resources，保留脱敏失败阶段/原因，O5 flat；不得尝试命令面或扩大公网暴露面。

## 7. 留档顺序

当前只完成 `pre_start.md -> prd.md -> tech-plan.md`。Engineer 实现、测试和一次 live capture 后才能创建 `tech-done.md`；Product 验收后再创建 `side2side_check.md` 与 `final.md`。
