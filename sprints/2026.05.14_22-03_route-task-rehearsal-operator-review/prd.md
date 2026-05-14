# Sprint 2026.05.14_22-03 Route Task Rehearsal Operator Review - PRD

sprint_type: epic

## 用户价值和产品北极星

产品北极星是让普通手机用户可以完成送垃圾任务，并在异常时让操作员/支持人员快速知道“发生了什么、还缺什么证据、下一轮该怎么重跑”。本轮不追求新的云材料或硬件证明，而是把 route/task rehearsal 的软件证据转成操作员可读的复盘/重跑决策。

直接用户是现场操作员和支持人员，间接受益用户是不会 ROS2、串口、Nav2 或 artifact 的普通手机用户。复盘能力必须减少人工翻 raw JSON、路径文件或命令日志的成本，同时保持安全边界：它不能启用控制按钮，不能泄露内部材料，不能把 metadata、ACK 或 artifact pass 说成 delivery success。

## OKR 映射

### Objective 2：可送垃圾任务完整闭环

本轮推进 KR5 的“每次任务产出可复盘记录”，但边界是 Docker/local software proof。operator review 必须说明任务闭环仍缺真实 Nav2/fixed-route、真实 dropoff/cancel completion、真实 failure recovery 和真实 delivery success。

### Objective 3：可验证导航与固定路线

本轮推进 KR3/KR5 的 dry-run/replay 与关键状态可解释能力。operator review 要把 route status、task record、crosscheck、HIL alignment 和 mismatch 摘要整合成下一轮 rehearsal decision，帮助下一步从 software replay 走向真实路线/任务证据。

### Objective 5：云中转 + OSS/CDN 数据通路产品化

Objective 5 约 68% 且数字最低，但需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 材料。本轮只允许将 operator review 的 phone-safe 摘要展示在 diagnostics/mobile surface，不新增 O5 completion claim。

### Objective 1：硬件协议可信底盘

本机只有 Docker，没有真实硬件。本轮不读取 WAVE ROVER、UART、Orange Pi、launch 硬件参数，不声明 HIL、真实串口、底盘 feedback、`/odom`、`/imu/data` 或 `/battery` 实机证据。

## KR 拆解或更新

- KR-O2-review：从 execution bundle 生成可复盘 operator review package，包含 `evidence_ref`、crosscheck 状态、HIL alignment `not_proven`、mismatch 摘要、缺材料和下一轮动作建议。
- KR-O3-decision：形成 `next_rehearsal_decision`，把“继续本地 bundle 包装”替换为“补 route/task material、重跑 rehearsal、准备真实 route/Nav2/fixed-route 证据或等待真实 HIL 材料”的明确分支。
- KR-mobile-safe：Robot diagnostics 与 `mobile/web` 只展示 phone/support-safe 字段，复制内容 whitelist-only，控制按钮继续 fail-closed。
- KR-boundary：所有产物统一 evidence boundary 为 `software_proof_docker_route_task_rehearsal_operator_review_gate`，并保留 `not_proven`，不得写成 HIL、真实路线运行、dropoff/cancel completion 或 delivery success。

## 本轮核心抓手

将 `route_task_rehearsal_execution_bundle.json` 升级为可消费的操作员复盘包：

- 输入：上一轮 execution bundle manifest，及其脱敏 artifact/crosscheck/HIL alignment 摘要。
- 输出：operator review package，schema 建议为 `trashbot.route_task_rehearsal_operator_review.v1`。
- 展示：diagnostics summary 与 `mobile/web` 首屏/诊断附近的 phone-safe review panel。
- 控制：metadata-only，不新增或放开任何 Start/Confirm/Cancel/ACK/cursor 路径。

## 需要做什么

### Task A - Autonomy Operator Review Package

`autonomy-engineer` 新增或扩展 `pc-tools/evidence/` 下的 operator review/report 生成器。它只读消费 `route_task_rehearsal_execution_bundle.json`，输出 phone/support-safe package。必须包含：

- `schema=trashbot.route_task_rehearsal_operator_review.v1`
- `evidence_boundary=software_proof_docker_route_task_rehearsal_operator_review_gate`
- `evidence_ref`
- `crosscheck_status`
- `hil_alignment_status=not_proven` 或保守 blocked/missing
- mismatch 摘要
- `next_rehearsal_decision`
- `not_proven`
- `safe_copy`

禁止读取硬件、触发 Nav2、访问串口、执行机器人控制或把 execution bundle 解释为真实路线/送达成功。

### Task B - Robot Diagnostics Summary

`robot-software-engineer` 让 `operator_gateway_diagnostics.py` 只读消费 operator review package，生成 diagnostics summary。summary 必须能处理 missing、read_error、unsupported schema、crosscheck fail、unsafe copy 等保守状态。metadata-only 必须不触发：

- Start/Confirm/Cancel enablement
- ACK POST
- cursor/persistence
- HIL
- dropoff/cancel completion
- delivery success

### Task C - Full-stack Mobile Review Surface

`full-stack-software-engineer` 在 `mobile/web` 首屏或诊断附近渲染 route/task rehearsal operator review 摘要。页面只能消费 `/api/status`、`phone_readiness`、`/api/diagnostics` 中的 phone-safe 字段。复制/展示内容必须 whitelist-only，不能泄露 artifact/raw path、local path、credentials、ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER、traceback、checksum、complete artifact 或 raw robot response。

Start Delivery、Confirm Dropoff、Cancel 保持 fail-closed；operator review 不新增控制授权条件。

## 优先级和验收口径

P0：

- Operator review package 能从 execution bundle 生成，包含核心复盘字段和 `next_rehearsal_decision`。
- Diagnostics 能只读消费 review package，并在所有异常输入下保守降级。
- `mobile/web` 能展示 phone-safe review 摘要，且主操作按钮保持 fail-closed。

P1：

- `safe_copy` 可直接给支持人员使用，字段 whitelist-only。
- 文档同步更新到相关 `docs/`，解释新 schema、证据边界和手机展示边界。

验收通过条件：

- 三个 owner 均完成各自 targeted validation。
- 围栏搜索必须命中 `software_proof_docker_route_task_rehearsal_operator_review_gate`、`not_proven` 和 delivery success 非证明边界。
- scoped `git diff --check` 通过。
- final 中明确是否更新 `OKR.md`。若只有软件复盘能力增强，O2/O3 可谨慎评估；O5/O1 不得因本轮上调。

## 对应责任 Engineer

- `autonomy-engineer`：operator review/report generator、CLI drill、navigation docs。
- `robot-software-engineer`：diagnostics consumer、metadata-only tests、interface docs。
- `full-stack-software-engineer`：`mobile/web` review panel、phone-safe fixture/tests、product docs update。
- `product-okr-owner`：阶段验收、sprint closeout、OKR 边界与 `OKR.md` 更新判断。

## 风险、阻塞和证据链

- O5 阻塞：缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration。
- O1 阻塞：本机只有 Docker，缺真实 WAVE ROVER、真实串口、`T=1001` feedback 和 HIL。
- O2/O3 证据缺口：仍缺真实 Nav2/fixed-route 实跑、真实路线采集、同一 `evidence_ref` 的上车复账、真实 dropoff/cancel completion 和 delivery success。
- 产品风险：如果 review panel 文案过强，会把软件复盘误读成真实送达或硬件通过；必须使用 `not_proven` 和 accepted/processing-only 语义。
- 安全风险：任何 copy/export 必须 whitelist-only，默认 `safe_to_control=false`。

## 需要创建或更新的 sprint 文档

本阶段已创建 `pre_start.md`、`prd.md`、`tech-plan.md`。工程实现后必须更新 `tech-done.md`；验收后更新 `side2side_check.md` 与 `final.md`。如实际改动触及 docs 口径，相关 `docs/` 文件必须在各 owner 任务内同步更新。
