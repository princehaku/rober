# Sprint 2026.05.13_03-04 Mobile Web Entrypoint Gate - PRD

## 背景

当前 rober 已经有本地 operator fallback 页面、phone readiness、command safety、offline/resume readiness、voice prompt readiness、support handoff 和 cloud-relay self-contained runtime 证明。但手机侧部署单位 `mobile/` 仍停留在 README 脚手架，正式手机 PWA 入口还没有落到 `mobile/web/`。

这导致 Objective 4 的主要缺口仍然存在：普通手机用户没有一个可运行、可部署、可验收的手机入口。继续加强云中转 backend 会让 O5 变厚，但不会直接解决 O4 的低完成度缺口。

## 用户价值和产品北极星

用户价值：

- 手机用户打开入口后能先看到是否可继续、哪里被阻断、下一步该做什么。
- 弱网、离线、等待 ACK 或人工接管时，用户仍能看到诊断/求助入口，而不是误触发 Start/Confirm/Cancel。
- 用户不需要看到 raw JSON、ROS topic、串口、WAVE ROVER 参数、密钥、DB/queue URL 或本地路径。

产品北极星：

- 手机是普通用户唯一入口，云中转是正式 4G 路径，本地 operator gateway 是 fallback 调试入口。
- 本轮从 fallback 内嵌页面推进到 `mobile/web/` dependency-free PWA entrypoint，但证据边界仍是 Docker/local software proof。

## OKR 映射

Primary: Objective 4 - 建立手机用户体验与低成本量产边界。

- KR1：把手机端最小流程从文档和 onboard fallback 推进到 `mobile/web/` 可运行入口。
- KR4：继续消费诊断最小数据包和 phone-safe support/diagnostics summary。
- KR5：普通用户不接触命令行、ROS2、串口或 raw JSON，也能理解阻断原因和恢复路径。
- KR7：为后续真实手机验收提供独立 PWA 静态入口、离线 shell、manifest/service worker 和基础可用性 smoke。

Secondary: Objective 5 - 云中转 + OSS/CDN 数据通路产品化。

- 只作为 contract compatibility guardrail：手机入口消费 commands/status/ack 相关 phone-safe schema，但不改变 cloud-relay command/status/ack 语义。

## KR 拆解

### KR-A: 独立手机 PWA 入口

- 在 `mobile/web/` 形成 dependency-free 静态入口。
- 至少包含 `index.html`、CSS、JS、`manifest.webmanifest`、`service-worker.js`、offline shell，以及 worker 认为必要的 fixture/smoke helper。
- 入口能在静态服务或简单本地文件验证中展示手机主流程。

### KR-B: Phone-safe schema 消费

- 只读取 `/api/status`、`/api/diagnostics` 中已有 phone-safe 字段。
- 明确消费 `phone_readiness`、`command_safety`、`phone_offline_resume_readiness`；可按已有 docs 消费 `voice_prompt_readiness`、`phone_support_bundle`、`phone_task_flow_readiness`。
- 不新增机器人状态名，不把 fixture 当实时状态，不展示 raw ROS/hardware/cloud secret details。

### KR-C: 操作安全和离线恢复

- Start Delivery、Confirm Dropoff、Cancel 的 enabled/disabled 由 `command_safety` 和既有 action permission 决定。
- Offline shell 必须保持 primary actions disabled，不缓存或重放控制请求。
- Diagnostics 和 Support Handoff 可在 primary actions blocked 时继续可达。

### KR-D: Remote bridge/operator compatibility fence

- 新 static contract 或 mobile metadata 不污染 `trashbot.remote.v1` command/status/ack envelope。
- Metadata-only response 不触发 robot action、不 ACK、不推进 cursor、不持久化 cursor。
- ACK 文案保持 accepted/processing evidence only，不等于 delivery success。

### KR-E: 文档同步

- 更新 `mobile/README.md`，说明 `mobile/web/` 当前实际入口、运行方式、schema 消费边界和非证明项。
- 更新 `docs/product/mobile_user_flow.md`，把正式 mobile web entrypoint 与本地 fallback 区分清楚。
- 更新 `docs/interfaces/ros_contracts.md`，补充 mobile web 作为 consumer 的 contract，不改变 ROS2/remote envelope 语义。

## 范围边界

In scope:

- `mobile/web/` dependency-free PWA entrypoint。
- Phone-safe schema 消费和本地 fixture/smoke。
- PWA manifest、service worker、offline shell。
- Operator/static 或 remote bridge compatibility fence 所需的最小测试。
- `mobile/README.md`、`docs/product/mobile_user_flow.md`、`docs/interfaces/ros_contracts.md` 同步。

Out of scope:

- 真实 iPhone/Android 设备验收。
- 真实公网云、HTTPS/TLS、4G/SIM、OSS/CDN 实流量。
- Native app、登录系统、账号体系、推送通知。
- ROS2 行为状态机、Nav2/fixed-route、WAVE ROVER、UART、HIL 或真实送达。
- 改变 `trashbot.remote.v1` command/status/ack envelope。

## 优先级

- P0：`mobile/web/` 可运行入口 + phone-safe schema 消费 + primary actions 安全阻断。
- P0：remote bridge compatibility fence，确保 mobile metadata 不触发机器人动作或 ACK。
- P1：offline shell、manifest/service worker、fixture/smoke helper。
- P1：产品与接口文档同步。
- P2：视觉 polish 和额外布局细节；不得牺牲 P0/P1 安全边界。

## 验收口径

本轮验收通过的最小标准：

- `mobile/web/` 存在可运行 dependency-free 入口，且静态 smoke 可验证关键资源和 schema 消费边界。
- 页面只展示 phone-safe copy，不暴露 raw JSON、ROS topic、串口、baudrate、WAVE ROVER 参数、token、Authorization、OSS AK/SK、DB/queue URL、local path、checksum 或完整 artifacts。
- command buttons 在 blocked/offline/pending ACK/manual takeover 状态保持 disabled；Diagnostics/Support Handoff 仍可达。
- service worker 明确绕过 `/api/*`、robot/command/ACK/diagnostics 和非 GET 控制流量。
- remote bridge/operator compatibility fence targeted unittest 通过，确认 metadata-only contract 不触发 action、不 ACK、不推进 cursor。
- 文档同步完成，并明确 evidence boundary 是 `software_proof_docker_mobile_web_entrypoint_gate`。

## 责任 Engineer

- `full-stack-software-engineer`：实现 KR-A/B/C/E 中手机入口和文档同步。
- `robot-software-engineer`：实现 KR-D 的 compatibility fence 和接口边界文档说明。

## 风险、阻塞和证据链缺口

- 真实手机浏览器/设备未接入，因此不能 claim production app 或 real device acceptance。
- 真实云/4G/OSS/CDN 未接入，因此不能 claim production cloud path。
- 本机没有真实硬件，因此不能 claim WAVE ROVER motion、UART feedback、HIL、Nav2/fixed-route 或 delivery success。
- 如果 worker 需要修改现有 onboard fallback 页面，必须保持 backward compatibility，并用 targeted operator gateway tests 覆盖。
