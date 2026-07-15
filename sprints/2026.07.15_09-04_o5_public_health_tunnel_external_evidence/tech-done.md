# Tech Done - O5 Public Health Tunnel External Evidence

## 1. 状态与证据边界

- `sprint_type: epic`
- Delivery owner：`full-stack-software-engineer`
- 实现状态：本地 health-only 安全链路完成并验证；唯一一次 live invocation 已执行且在公网 capture 前 fail closed。
- Live 结论：`blocked_provider_runtime_preflight_before_tunnel_start`。
- `capture_invocation_count=1`、`public_capture_count=0`、`tunnel_start_attempt_count=0`、`public_probe_attempt_count=0`。本次唯一 invocation 在官方 metadata 成功之后、SHA256/version 完整 gate 之前收到 remote command exit `1`；因此没有 public URL，没有 TLS/certificate、GET/HEAD 或公网负向请求。按“唯一 live 不重跑”约束停止，不为追求 clean 结果开第二个 tunnel。
- Proof boundary：`software_and_failed_live_preflight_o5_public_health_tunnel_external_evidence`。它证明本地 allowlist/loopback 合同和一次真实 provider runtime 前置尝试；不证明 public HTTPS success、稳定 DNS、4G、production DB/queue、worker、OSS/CDN、真手机、route、delivery、HIL 或 `safe_to_control`。

## 2. 用户旅程变化与触点收益

开发/运维人员现在有一个明确的只读公网健康边界：relay 主机端口固定发布到 `127.0.0.1`，临时 tunnel 只能指向独立 proxy；proxy 仅允许精确 `GET /healthz` 与 `HEAD /healthz`。`/readyz`、`/preflightz`、status、command、archive、query、编码、双斜杠和 absolute-form 等入口在到达 relay 前 fail closed。

本轮没有获得真实公网在线证据，用户不能据此判断公网 health 已可用。实际收益是把过去“tunnel 可误连整个 relay”的风险收紧为可测试的 health-only contract，并留下不含 URL/credential 的失败 artifact 和 cleanup 事实，避免失败后遗留公开入口。

## 3. 实际改动

1. `cloud-relay/scripts/healthz_allowlist_proxy.py`
   - 新增纯 Python 标准库 loopback proxy CLI；listen/upstream host 必须字面为 `127.0.0.1`。
   - 只允许原始 target 精确为 `/healthz` 的 GET/HEAD；HEAD 以固定 upstream GET 验证，但公网 body 长度为 `0`。
   - 负向 path 返回 `404`；精确 health 的 POST/PUT/PATCH/DELETE/OPTIONS/TRACE/CONNECT 返回 `405` 和 `Allow: GET, HEAD`。
   - 不转发客户端 Authorization、Cookie、Host、Forwarded、X-Forwarded-* 或 body；upstream path 固定为 `/healthz`。
   - 增加 target/header/upstream body/timeout 上限，upstream timeout/error 固定脱敏为 `504/502`。
   - 纯 `#` 中文注释行占非空行 `22.0%`，满足项目 `>20%` 围栏。
2. `cloud-relay/test/test_healthz_allowlist_proxy.py`
   - 新增 6 个回归测试，覆盖 GET/HEAD、全套负向 path/query/encoding/absolute-form、method gate、敏感 header 隔离、upstream timeout/error 和非 loopback 配置拒绝。
   - 负向测试同时断言 fake upstream request count 不变，证明不是仅返回状态码而实际穿透。
   - 纯 `#` 中文注释行占非空行 `21.8%`。
3. `cloud-relay/docker-compose.yml`
   - host publish 从 all-interface 收紧为 `127.0.0.1:${TRASHBOT_REMOTE_CLOUD_PUBLISHED_PORT:-8088}`。
   - 保持 bearer token fail-closed 必填合同；本地 compose 结构检查和 loopback smoke 也必须显式注入一次性非生产 token，共享主机/production 必须使用独立 secret。
4. `cloud-relay/README.md`
   - 同步 loopback 迁移影响、proxy 启动示例、cloudflared 只能指向 proxy 的 `NO-GO`、方法/路径/header/body 边界及 temporary proof 限制。
5. `artifacts/full-stack/live_capture_helper.py`
   - 新增 one-shot helper：官方 HTTPS API/release ARM64 provenance、SSH staging、process-group ownership、默认 CA TLS probe、固定负向矩阵、state checksum、redaction 和 finally cleanup。
   - output 已存在时拒绝覆盖；远端进程带 `timeout`，raw public URL 只允许在运行内存/临时日志中出现。
   - 纯 `#` 中文注释行占非空行 `23.1%`。
6. `artifacts/full-stack/public-health-tunnel-evidence.json`
   - 保存唯一 invocation 的脱敏失败事实、四个 delta、安全 false 字段与 `cleanup_residual_count=0`；不含 raw URL、hostname、token、header、body、tunnel log 或绝对路径。

## 4. 接口影响

- 新增本机 CLI：`healthz_allowlist_proxy.py --listen-host/--listen-port/--upstream-host/--upstream-port`。
- relay `/healthz` schema、原有 GET/POST route、bearer contract、state schema 和 ROS2 interface 均未修改；compose 继续要求显式非空 `TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN`，没有弱化默认鉴权。
- compose 的主机端口不再允许 LAN/all-interface 直连；本地仍使用 `127.0.0.1:8088`。过去依赖 LAN 访问 `8088` 的开发流程必须改为受控反向代理，不能重新放宽 compose publish。
- 本轮没有新增公网 API、command/task/status/archive/control 能力。

## 5. 本地验证与修复记录

### 5.1 首轮失败与修复

- 首轮无环境变量执行 `docker compose -f cloud-relay/docker-compose.yml config >/dev/null` 因 `${TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN:?...}` 拒绝插值；这是预期的 fail-closed 合同行为，不应通过提供默认 token 绕过。
- 集成窄修：恢复 `${TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN:?set-dev-placeholder-token}`；README 明确本地结构检查/loopback smoke 必须显式传一次性非生产 env，共享主机/production 必须使用独立 secret。
- 注释围栏首轮按纯 `#` 行统计为 proxy `8.4%`、test `6.7%`；补充有意义的中文安全原因说明后为 `22.0%` / `21.8%`。helper 为 `23.1%`。

### 5.2 验证结果

- `python3 -m py_compile cloud-relay/scripts/healthz_allowlist_proxy.py cloud-relay/test/test_healthz_allowlist_proxy.py`
  - exit `0`。
- `python3 -m unittest cloud-relay/test/test_healthz_allowlist_proxy.py`
  - 初次交付 `Ran 6 tests in 5.555s`，集成窄修复验 `Ran 6 tests in 5.549s`；均为 `OK`。
- `python3 -m unittest discover -s cloud-relay/test -p 'test_healthz_allowlist_proxy.py'`
  - `Ran 6 tests in 6.057s`，`OK`。
- `TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=local-structure-check-only docker compose -f cloud-relay/docker-compose.yml config >/dev/null`
  - 显式注入本地结构检查 token 后 exit `0`；未设置 token 仍会按合同拒绝。
- helper `python3 -m py_compile`、`--help`、scoped `git diff --check`
  - 全部 exit `0`。
- 集成窄修本地验收：三文件 `py_compile`、显式 `local-structure-check-only` token 的 compose config、artifact `json.tool`、计数/delta/cleanup/redaction 断言和 scoped `git diff --check` 全部 exit `0`。
- 集成窄修没有执行 SSH、provider、tunnel 或第二次 live；既有事实保持 `capture_invocation_count=1`、`public_capture_count=0`。
- Live 后远端只读 residual 复核：目标进程列表为空；`/tmp/rober-o5-health-*` 目录计数 `0`。

## 6. 唯一 Live Capture 事实

执行入口严格使用计划中的 SSH target/port、`expected-arch=aarch64`、provider `cloudflare` 和本 sprint output。

- invocation count：`1`；public capture count：`0`；不再执行第二次 invocation 或 public capture。
- remote architecture：live 前重新确认 `aarch64`。
- official metadata：HTTPS API 成功，release version=`2026.7.1`，精确 ARM64 standalone asset/digest gate 已进入。
- failure：official metadata 成功后、`sha256_verified=true` 与 version gate 完成前，remote staging/binary gate command exit `1`。helper 的当前失败分类没有保留该 remote stderr（避免路径/URL 泄漏），因此不能进一步把本次失败安全归因为 download、chmod 或 binary execution 的某一个子步骤。
- tunnel：未启动，`tunnel_start_attempt_count=0`；没有 raw public URL。
- public TLS/certificate：未运行，`tls_certificate_valid=false` 代表 `not_run`，不是证书已被判无效。
- GET/HEAD：均 `not_run`，没有 success class。
- negative matrix/state checksum：均未运行；`state_unchanged=false` 代表 `not_run_before_provider_gate_failed`，不是已观察到 state mutation。
- cleanup：`cleanup_residual_count=0`，远端复核无本轮进程、无 helper 临时目录。
- 禁止动作：command/task/archive write/manual/`cmd_vel`/UART/route/delivery/HIL 全部未执行。

## 7. Delta、OKR 建议与剩余风险

- `current_run_artifact_delta=false`
- `external_artifact_delta=false`
- `live_control_delta=false`
- `user_action_delta=false`
- `production_ready=false`
- `mission_objective_0_satisfied=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `safe_to_control=false`

建议 O5 保持约 `85%`，KR `不归档`。本轮没有得到 certificate-valid public GET/HEAD 或公网负向矩阵，不能接受计划中的 `85% -> 86%`。

剩余风险与后续边界：provider runtime 子阶段仍缺可安全定位的 exit-stage 细分；本 sprint 已消费唯一 live 次数，不得在本轮重跑。若 Product/CEO 后续明确授权新的 sprint，应先让 helper 对 download、SHA、chmod、version 各写枚举化 stage（仍不保留 stderr/raw URL），完成纯 provenance dry gate 后再决定是否允许新的单次 public capture；不得用本轮失败包装出 O5 增量。
