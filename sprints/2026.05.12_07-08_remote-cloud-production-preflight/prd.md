# Sprint 2026.05.12_07-08 Remote Cloud Production Preflight - PRD

## 状态

- 阶段：prd
- 创建时间：2026-05-12 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 支撑 Engineer：`robot-software-engineer`
- 证据边界：目标为 `software_proof_docker_preflight_gate`

## 用户价值和产品北极星

本轮要把 O6 从“Docker relay 可以跑”推进到“真实云上线前置风险可被自动拦截”。对普通手机用户的价值是间接但关键的：未来云入口即使还没有接真实 4G 或真实机器人，也不能带着缺失 TLS、错误公网入口、占位凭证、不可写状态存储、OSS/CDN 配置缺口或敏感字段泄露进入生产路径。

北极星仍是普通用户只用手机，通过 4G 云中转完成 trash delivery。当前 PRD 不把 preflight/gate 包装成真实云部署完成，不把 command ACK 包装成真实送达，不把 Docker-only evidence 包装成 4G、OSS/CDN、Nav2、WAVE ROVER 或 HIL 证据。

## 背景和证据

1. `OKR.md` 2026-05-12 07:00 快照：
   - O6 约 27%，是当前最低且 Docker-only 主机可推进的目标。
   - O5 约 33%，主要缺正式手机 UI 和普通用户验收；本轮只提供 phone-safe 输出支撑。
   - O1/O2/O3/O4 完成度更高，但当前主机无真实硬件、真实路线、真实相机、真实 4G 或 HIL，不适合作为本轮主线。
2. `sprints/2026.05.12_06-07_remote-cloud-entry-docker-deploy/final.md`：
   - 已有 `software_proof_docker_deploy`。
   - 明确缺真实云 HTTPS/TLS、公网入口、防火墙、production secret provisioning、OSS/CDN、真实 4G/SIM、生产 DB/queue。
3. 近期 remote cloud 链路已具备：
   - independent relay service。
   - bearer auth。
   - file-backed persistence。
   - phone-safe errors。
   - Dockerfile/compose/env。
   - `/healthz`、`/readyz` 和 Docker smoke。
4. 当前产品风险：
   - 如果下一步直接上真实云，缺口会分散在配置、凭证、TLS、公网、防火墙、对象存储、状态恢复和手机输出多个面。
   - 需要先把这些缺口集中成一个 gate，明确 pass/blocked/warning 和剩余证据。

## OKR 映射

| KR | 本轮产品诉求 |
| --- | --- |
| O6 KR1 云中转服务端最小契约 | Gate 不改变 `trashbot.remote.v1` commands/status/ack；只增加上线前置检查。 |
| O6 KR2 云服务端基线 | 检查 4C 8G、公网入口、HTTPS/TLS、防火墙、运维边界的配置准备度和缺口。 |
| O6 KR3 OSS 写入策略 | 检查 bucket、region、object prefix、credential mode 是否符合目标形态；缺真实账号时返回 blocked/warning。 |
| O6 KR4 CDN 只读入口 | 检查 CDN base URL、公开只读视图边界和私有数据不走 CDN 的配置口径。 |
| O6 KR5 凭证管理 contract | 检查 env 注入、`.env.example` 占位、真实 secret 不入仓库、不进输出和 rotate/provisioning 缺口。 |
| O6 KR6 graceful degradation | Gate 输出必须能区分网络/配置/凭证/状态存储/OSS-CDN 缺口，并给出 phone-safe retry hint。 |
| O5 KR5/KR7 支撑项 | 只沉淀用户可读安全状态，不交付正式手机 UI。 |

## KR 拆解或更新

### P0 - Production config preflight

- 检查 relay contract、public base URL、expected scheme、host binding、port、environment profile、robot id namespace。
- 对占位值、缺失值、local-only 值给出明确 `blocked` 或 `warning`。
- Docker-only 环境可以预期返回“真实公网/TLS 未配置”的 blocked，不要求伪造 production pass。

### P0 - Secret and credential preflight

- 检查 bearer token、OSS credential mode、future STS/limited AK 配置是否通过环境变量或 secret provider 注入。
- `.env.example` 只能出现占位。
- Gate 输出、state file、错误响应不得回显真实 token、Authorization header、OSS AK/SK、root password 或 credential-bearing URL。

### P0 - TLS/public ingress/firewall preflight

- 检查是否配置 HTTPS public base URL、TLS certificate reference、reverse proxy/ingress mode、防火墙策略说明或环境变量。
- 当前 Docker local 只能证明服务形态，不得标记为 public ingress ready。
- 输出需要区分 `local_only`、`tls_missing`、`public_ingress_missing`、`firewall_unverified` 等原因。

### P0 - OSS/CDN preflight

- 检查 `bucket=bytegallop`、`region=oss-cn-hangzhou`、对象前缀 `rober/<robot_id>/<date>/<task_id>/` 形态、CDN base URL `https://cdn.bytegallop.com/rober/`。
- 检查私有任务数据不直接走公开 CDN 的边界。
- 缺 STS、受限 AK 或真实 OSS reachability 时不能标记为真实对象链路通过。

### P0 - State store and recovery preflight

- 检查 state store 配置、可写性、原子写入/恢复语义、备份/多实例缺口。
- 允许 file-backed proof 继续存在，但必须输出“不等于 production DB/queue”的风险。
- Gate 不能把 ACK/cursor 恢复等同于真实 delivery result。

### P0 - Phone-safe output

- 输出字段应适合手机端或 operator 页面使用，例如 `overall_state`、`checks[]`、`status`、`reason`、`safe_summary`、`retry_hint`、`evidence_boundary`。
- 不暴露 raw traceback、ROS topic、串口、baudrate、WAVE ROVER 参数、`/cmd_vel` 或底层速度入口。
- 错误分类以用户可理解问题为主：配置缺失、凭证未配置、TLS 未配置、公网未验证、OSS/CDN 未验证、状态存储不可写。

## 做什么 / 不做什么

做：

- 定义并实现真实云前置 gate。
- 复用已有 Docker relay/readiness 能力，避免重新发明一套服务。
- 用少量 targeted validation 证明 gate 输出、敏感字段过滤和已有 remote contract 不退化。
- 在当前 sprint 后续 `tech-done.md` 记录 gate 的 pass/blocked/warning 样例。

不做：

- 不部署真实云，不购买域名，不申请证书，不实配防火墙。
- 不接真实 4G/SIM，不跑 carrier 弱网实测。
- 不完成 OSS/CDN 上传、STS 发放、CDN 回源、生命周期或 rotate 实流量。
- 不迁移生产 DB/queue，不验证多实例一致性、备份或灾备。
- 不做正式手机 UI、美观验收、普通用户实机验收。
- 不修改硬件、Nav2、fixed-route、WAVE ROVER 或 HIL 相关实现。

## 优先级和验收口径

| 优先级 | 用户可感知价值 | 验收口径 |
| --- | --- | --- |
| P0 Config gate | 上线前知道缺哪些生产配置 | Docker-only 主机能运行 gate，并输出明确 pass/blocked/warning。 |
| P0 Secret gate | 避免密钥泄露给仓库、日志或手机 | 示例 env 和 gate 输出不含真实 secret 或 Authorization header。 |
| P0 TLS/public gate | 避免把 local Docker 当真实公网 | local-only/TLS missing/public ingress missing 能被识别。 |
| P0 OSS/CDN gate | 避免图片链路配置错误后才发现 | OSS/CDN 目标配置形态可检查，真实链路缺口被保守标记。 |
| P0 State gate | 避免状态不可写或恢复边界不清 | state store 可写性和 production DB/queue 缺口有明确输出。 |
| P0 Phone-safe output | 手机端未来能显示安全、可理解状态 | 输出不含底层硬件/ROS/密钥细节，有 safe summary 和 retry hint。 |
| P1 Docs/sprint evidence | 后续团队能按证据继续真实云部署 | `tech-done.md` 记录命令、输出、失败定位和剩余风险。 |

## 对应责任 Engineer

- 主责：`full-stack-software-engineer`
  - production preflight/gate 实现。
  - 配置、凭证、TLS/公网、OSS/CDN、state store、phone-safe 输出。
  - 相关 targeted tests/smoke 和当前 sprint `tech-done.md`。
- 支撑：`robot-software-engineer`
  - 复核 remote bridge / robot client compatibility。
  - 确认 ACK/cursor/conservative failure 语义不被 gate 误写成 delivery result。
- Product Acceptance：`product-okr-owner`
  - 检查 O6 证据边界。
  - 维护后续 `side2side_check.md`、`final.md` 和必要 OKR 保守更新。

## 风险、阻塞和需要补齐的证据链

- 如果真实云/TLS/OSS/CDN/生产 DB 配置缺失，gate 应输出 blocked；这不是失败，而是本轮目标的一部分。
- 即使 gate 在 Docker-only 环境通过所有 local checks，也不等于真实云公网、HTTPS/TLS、防火墙、4G/SIM、OSS/CDN 实流量或生产 DB 已验证。
- O5 只能获得 phone-safe 输出支撑；正式手机 UI 不在本轮验收范围。
- O1/O2/O3/O4 不因本轮 gate 变化提升。
- 若后续实现修改代码，必须保持中文技术注释规范，并在需要时同步 `docs/product/`。
