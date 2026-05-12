# Sprint 2026.05.13_05-06 Mobile Task Start Confirmation Gate - Side2Side Check

## 验收结论

- Product Owner 验收结论：通过阶段验收。
- 验收边界：`software_proof_docker_mobile_task_start_confirmation_gate`。
- 本轮只证明 Docker/local 软件合同：手机静态入口发车前具备 destination confirmation、loaded confirmation、`command_safety`、`can_collect` 四重 gate，且 `POST /api/collect` 使用 phone-safe JSON body，并同时携带同值 `destination`/`target` 以兼容现有 collect 入口。
- 本轮不证明真实手机设备/浏览器、production app、真实云/4G、OSS/CDN live traffic、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

## 用户价值和产品北极星核对

用户价值：普通用户在手机发车前必须确认"送到哪个垃圾站"和"垃圾已经放入车上"，降低误发车、空车发车、发错目的地和售后解释成本。

产品北极星：手机继续作为普通用户唯一入口；用户不需要理解 ROS2、raw JSON、云队列、串口、WAVE ROVER 或 ACK 细节。ACK 只解释为 accepted/processing evidence，不解释为送达成功。

## OKR 映射核对

- Objective 4 KR1：已补齐手机最小流程中的"选择/确认垃圾站 -> 确认已放入垃圾 -> 一键发车"软件 gate。
- Objective 4 KR5：Start blocked、缺 destination、未确认装载、后端缺 gate 时均 fail closed，用户能看到中文阻塞原因。
- Objective 4 KR7：本地手机入口主路径继续中文优先，并以静态 smoke 覆盖按钮与 payload 合同；仍缺真实手机设备/浏览器验收。
- Objective 2 guardrail：Robot compatibility fence 证明 phone confirmation metadata 不触发 backend action、不 POST ACK、不推进 cursor，不把 ACK 升级为 delivery success。
- Objective 5 guardrail：payload 只作为 UI/API 用户确认记录，不证明真实云、4G、OSS/CDN 或 production queue。

## Worker 结果对照

### Full-stack

- 已在 `mobile/web` 增加发车确认区、destination gate、loaded confirmation checkbox 和 Start 阻塞原因。
- Start Delivery 同时受 destination、loaded confirmation、`command_safety.actions.start.enabled=true`、`can_collect=true` 四重 gate 控制。
- `/api/collect` 从 body-less POST 升级为 `Content-Type: application/json` 的 phone-safe payload，payload 同时包含 `destination` 与同值 `target`。
- Product Owner 重跑 mobile smoke 结果：`Ran 6 tests in 0.001s`，`OK`。

### Robot

- 已增加 remote bridge/protocol compatibility fence。
- metadata-only phone confirmation 不触发 backend action、不 POST ACK、不推进内存 cursor、不持久化 cursor。
- protocol fence 证明 metadata 不污染 `trashbot.remote.v1` normalized command envelope。
- Product Owner 重跑 remote bridge/protocol targeted tests 结果：`Ran 64 tests in 32.606s`，`OK`；`py_compile` 通过。

## 引用路径核对

以下本轮引用路径均存在：

- `docs/product/mobile_user_flow.md`
- `docs/product/remote_4g_mvp.md`
- `docs/interfaces/ros_contracts.md`
- `docs/process/okr_progress_log.md`

## 验收口径

通过：

- Start Delivery 不再是 body-less collect POST。
- collect payload 同时包含 `destination` 和同值 `target`，兼容现有 `/api/collect` 读取 `body.target` 的服务端逻辑。
- 缺 destination、未确认 loaded、`command_safety` 不允许或 `can_collect=false` 均不能发车。
- payload 不暴露 ROS topic、`/cmd_vel`、serial device、baudrate、WAVE ROVER 参数、credential、local path 或完整 diagnostics artifact。
- ACK 文案保持 accepted/processing evidence only。
- Robot 侧确认 phone metadata 不改变 command envelope、cursor 或 ACK 语义。

不计入：

- 真实手机设备/浏览器。
- production app。
- 真实云/4G。
- OSS/CDN live traffic。
- Nav2/fixed-route。
- WAVE ROVER、HIL 或真实送达。

## 剩余风险

- "已放入垃圾"仍是用户显式确认，不是自动载荷检测。
- 当前手机入口仍是 local/static software proof，未完成真实手机浏览器、PWA install prompt 或 production app 验收。
- Collect payload 与后端生产消费链仍需后续真实云/4G 和 production queue 证据。
