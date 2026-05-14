# Sprint 2026.05.14_18-19 Mobile PWA Install Prompt Evidence Export - PRD

sprint_type: epic

## 用户价值和产品北极星

普通用户和现场验收人员不应该通过开发者工具、日志或内部 JSON 去证明 PWA 安装提示状态。本轮要把已经捕获的 `beforeinstallprompt`、`beforeinstallprompt.userChoice`、`appinstalled` 状态，整理成手机端可见、可复制、可下载的现场验收材料包。

产品北极星：手机端是普通用户唯一入口；任何验收材料都必须用手机可理解的方式表达，并且不能让 support metadata 变成 robot control grant 或真实交付证明。

## 背景证据

- `OKR.md` 4.1：Objective 5 约 68%，但下一步需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration，本机 Docker-only 环境不可补齐。
- `OKR.md` 4.1：Objective 4 约 94%，仍缺真实 iPhone/Android device behavior、production app、真实 PWA prompt/userChoice 现场验收。
- 上轮 `mobile_pwa_install_prompt_event_capture*` 已完成事件监听和事件证据包，但还缺一个面向现场验收的 export 材料包。

## OKR 映射

### Objective 4：手机用户体验与低成本量产边界

本轮直接服务 Objective 4 KR5 / KR7：

- KR5：用户验收标准要求普通用户不接触命令行、不插线调试、不理解 ROS2，也能知道失败时该怎么做。
- KR7：手机端 UI 美观且能直接使用，主流手机尺寸适配，当前 readiness gate 口径见 `docs/product/mobile_user_flow.md`。

本轮完成后，Objective 4 可以增加一条软件证据：`software_proof_docker_mobile_pwa_install_prompt_evidence_export_gate`。它证明 Docker/local mobile PWA 能导出 phone-safe 验收材料，不证明真实设备验收。

### Objective 5：云中转 + OSS/CDN 数据通路产品化

Objective 5 仍是最低完成度，但本轮不推进 O5。理由是 O5 当前缺口是外部材料，不是本地 metadata 能解决：

- 真实公网 HTTPS/TLS
- 真实 4G/SIM
- OSS/CDN live traffic
- production DB/queue connectivity
- production worker/migration

## KR 拆解或更新

本轮不直接修改 `OKR.md`，实现收口时由 Task C 根据证据更新。建议验收后采用以下 KR 口径：

- Objective 4 新增软件证据：`mobile_pwa_install_prompt_evidence_export*` 已形成 whitelist-only、phone-safe、可复制/下载的现场验收材料包。
- Objective 4 不得写成：真实 iPhone/Android behavior 已通过、production app 已通过、真实 PWA prompt/userChoice 已通过。
- Objective 5 保持不变，除非实现期间出现真实外部 O5 材料；本 sprint 当前不要求也不预期该材料。

## 本轮核心抓手

建立 `mobile_pwa_install_prompt_evidence_export*` family：

- export schema：`trashbot.mobile_pwa_install_prompt_evidence_export.v1`
- summary schema：`trashbot.mobile_pwa_install_prompt_evidence_export_summary.v1`
- copy schema：`trashbot.mobile_pwa_install_prompt_evidence_export_copy.v1`
- evidence boundary：`software_proof_docker_mobile_pwa_install_prompt_evidence_export_gate`

## 需要做什么

### Full-Stack 侧

- 在手机 PWA 中增加 PWA install prompt evidence export 面板或复用现有 PWA 安装提示证据区。
- 从 `mobile_pwa_install_prompt_event_capture*`、`mobile_pwa_install_prompt_evidence*`、handoff/device/browser proof 相关 phone-safe fields 派生 export summary。
- 支持一键复制和下载 JSON/text 材料包。
- 所有字段必须 whitelist-only，且缺真实设备或真实 prompt 时显示 `not_proven`。
- Start Delivery、Confirm Dropoff、Cancel 不得因为 export 状态启用。

### Robot 侧

- 为 `mobile_pwa_install_prompt_evidence_export*` family 增加 metadata-only compatibility fence。
- 证明 export payload 不触发 collect/dropoff/cancel、ACK POST、cursor advance/persistence、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success。
- 若 mixed payload 同时包含合法 `trashbot.remote.v1` command，仍只能由合法 command envelope 决定 robot action，export metadata 不得参与授权。

### Product 侧

- 收口 `tech-done.md`、`side2side_check.md`、`final.md`。
- 核对 `docs/product/mobile_user_flow.md` 是否已覆盖本轮新增 export 行为；若实现产生产品行为差异，要求对应 worker 在允许范围内补文档。
- 收口时更新 `OKR.md` 和 `docs/process/okr_progress_log.md`，但本计划创建阶段禁止改动这些文件。

## 优先级和验收口径

P0：

- export/copy/download material 只包含白名单字段。
- `safe_to_control=false`、`ack_semantics=accepted_processing_only_not_delivery_success`、`not_proven` 必须稳定出现。
- Start/Confirm/Cancel 继续 fail closed。
- Robot fence 证明 metadata-only export 不触发任何 robot control 或 delivery result。

P1：

- 手机 UI 文案中文优先，材料字段能被现场验收人员直接复测。
- download 文件名、schema、client reference、timestamp 能支持现场材料归档。
- 证据边界命名统一为 `software_proof_docker_mobile_pwa_install_prompt_evidence_export_gate`。

不做：

- 不启用 Start Delivery、Confirm Dropoff、Cancel。
- 不触发 robot 控制、ACK、cursor 或 terminal action。
- 不新增真实生产 app、真实外部云、4G/SIM、OSS/CDN live traffic、production DB/queue。
- 不把 Docker/local software proof 写成真实手机验收。

## 对应责任 Engineer

- Task A：`full-stack-software-engineer`
- Task B：`robot-software-engineer`
- Task C：`product-okr-owner`

## 风险、阻塞和需要补齐的证据链

- 真实 iPhone/Android behavior、production app、真实 PWA prompt/userChoice 仍需现场材料。
- Objective 5 外部证据仍缺，不在本轮闭环。
- export 材料一旦包含 raw payload、credential、ROS topic、`/cmd_vel`、serial、WAVE ROVER、local path、traceback、checksum 或完整 artifact，就必须判定失败。
- 若实现只做 UI 但没有 Robot metadata-only fence，不能收口为完整 sprint。

