# Sprint 2026.05.20_07-08 Hardware Sensor HIL-entry Callback Intake - PRD

sprint_type: epic

## 1. 产品问题

PR #5 review thread `PRRT_kwDOSWB9286CJ3tX` 仍要求 mandatory sensor assumptions cite local vendor sources and real materials。当前 repo 已能生成 `hardware_sensor_hil_entry_execution_pack`，但执行包之后没有回调入口承接真实现场材料。结果是现场 owner 即使拿到真实 2D LiDAR / ToF、mounting/wiring/power、calibration 或 HIL-entry operator result，也缺少一个 fail-closed、可复核、跨 PC / Robot / mobile 的回填路径。

本轮不解决真实材料本身；本轮已把入口落成 PC gate、Robot diagnostics safe alias 和 mobile/web 只读 panel。它仍只是 `software_proof_docker_hardware_sensor_hil_entry_callback_intake_gate`，不等于真实材料到位。

## 2. 用户价值和产品北极星

用户价值：

- 对 reviewer：能看到 PR #5 的 sensor assumptions 不再停留在本地 source packet，而是有真实材料 callback intake 的后续入口。
- 对现场 owner：执行包执行后可以按固定 checklist 回填材料，不需要在聊天、截图和本地路径里拼证据。
- 对普通手机用户和支持人员：只看到安全摘要、缺口和下一步，不看到 raw serial/UART、raw JSON、ROS topic、凭证、路径或完整内部 artifact。

产品北极星：让普通手机用户可理解、可支持地使用低成本 ROS2 小车完成送垃圾。硬件材料链必须可信且可追溯；没有真实材料和 HIL pass 前，所有传感器能力仍是 `software_proof` / `not_proven`。

## 3. OKR 映射

- Objective 1：主目标。围绕可信底盘和硬件材料边界，补齐 PR #5 / 2D LiDAR / ToF / HIL-entry 回调入口。该入口是未来真实材料提升 O1 的前置承接点，但 planning 本身不提高 O1。
- Objective 5：当前最低约 68%，但本 PRD 明确不推进 O5 completion。缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser 材料时，不继续做同一 O5 本地 wrapper。
- Objective 4：次要目标。mobile/web 需要用中文只读方式呈现 callback intake 状态，保持主操作 fail-closed。

## 4. KR 拆解或更新

### KR1 - Callback Intake Contract

定义 `hardware_sensor_hil_entry_callback_intake`，消费既有 `hardware_sensor_hil_entry_execution_pack` 和现场 callback materials，产出 artifact / summary。

必须字段：

- schema 和 schema_version
- `source=software_proof`
- evidence boundary
- safe `evidence_ref`
- source execution pack status
- accepted callback materials
- missing required materials
- rejected callback materials
- operator HIL-entry result summary
- next required evidence
- owner handoff
- `delivery_success=false`
- `primary_actions_enabled=false`
- `not_proven`

### KR2 - Material Acceptance Boundary

允许接收的材料类型必须是 sanitized 引用或摘要：

- 2D LiDAR SKU/source/receipt/procurement reference
- ToF SKU/source/receipt/procurement reference
- mounting plan / mounting photo reference
- wiring plan / wiring photo reference
- power budget / measurement reference
- calibration artifact reference
- HIL-entry operator result reference

禁止接收或透传：

- raw credentials、tokens、OSS AK/SK、DB/queue URL
- raw serial/UART device path、baudrate dump、raw JSON copy
- full local filesystem path、complete artifact、checksum
- HIL passed / field passed / delivery success copy
- Start / Confirm Dropoff / Cancel control authorization

### KR3 - Robot Diagnostics Safe Alias

Robot diagnostics 只消费 summary，不读取 raw callback material，不触发 ROS control、Nav2、HIL、ACK、cursor 或 command route。缺 summary、unsupported schema、weak boundary、success/control claims 时 fail closed。

### KR4 - Mobile/Web Read-only Panel

mobile/web 新增只读 “传感器 HIL 回调入口” panel。展示 callback intake status、safe `evidence_ref`、accepted/missing/rejected materials、operator result summary、owner handoff、next required evidence、`delivery_success=false`、`primary_actions_enabled=false` 和 `not_proven`。不改变 Start Delivery / Confirm Dropoff / Cancel gating。

## 5. 本轮核心抓手

Planning 阶段要把实现拆清楚，不让后续 worker 自行扩大范围。下一步实现必须是 3 个并行 worker：

1. Hardware PC gate：新增 gate、focused tests、README / product hardware boundary doc sync。
2. Robot diagnostics safe alias：新增 metadata-only consumer、focused tests、ROS contract doc sync。
3. Full-Stack mobile/web panel：新增只读 panel、fixture/test、mobile user flow doc sync。

## 6. 需要做什么

本轮已完成：

- 创建 sprint planning 目录。
- 写 `pre_start.md`、`prd.md`、`tech-plan.md`。
- 按 `tech-plan.md` 三个 worker 范围完成 Hardware PC gate、Robot diagnostics safe alias、Full-Stack mobile/web panel。
- Product closeout 补齐 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。
- 运行本轮 narrow integration validation。

本轮仍不做：

- 不跑 Docker colcon 或大构建。
- 不发布 GitHub reply，不 resolve PR thread。
- 不提高 OKR 百分比。

## 7. 优先级和验收口径

优先级：P0 planning blocker。只有该 planning 完成，下一轮 implementation 才能并行启动 Hardware / Robot / Full-Stack worker。

验收口径：

- 三份 planning 文件存在。
- 文档包含 Objective 5 / Objective 1 / PR #5 `PRRT_kwDOSWB9286CJ3tX` 背景证据。
- `tech-plan.md` 包含 `## OKR 最低优先级核对`。
- `tech-plan.md` 给出 Hardware PC gate、Robot diagnostics safe alias、Full-Stack mobile/web panel 三个并行 worker 任务。
- 所有边界保留 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 验证围栏只包含 file existence、required `rg` 和 scoped `git diff --check`。

## 8. 对应责任 Engineer

- Product Manager / OKR Owner：本轮 planning owner，负责 sprint 文档、产品边界、OKR rerank 和验收口径。
- Hardware Infra Engineer：后续 implementation owner 之一，负责 PC gate 和 vendor/source/material boundary。
- Robot Platform Engineer：后续 implementation owner 之一，负责 diagnostics safe alias。
- User Touchpoint Full-Stack Engineer：后续 implementation owner 之一，负责 mobile/web read-only panel。
- Autonomy Algorithm Engineer：本轮不需要改动；除非后续 callback material 涉及 Nav2/SLAM field evidence，否则只作为事实咨询。

## 9. 风险、阻塞和需要补齐的证据链

- 真实材料仍未提供，因此本 PRD 只能定义入口，不能产出真实 HIL 或 PR thread closure。
- 如果后续 worker 把 callback intake 写成 procurement complete、HIL pass、field pass 或 delivery success，必须 fail closed。
- 如果 O5 external materials 到位，应重新 rerank；否则继续避免 O5 local wrapper。
- 如果 reviewer 对 `PRRT_kwDOSWB9286CJ3tX` 追加新要求，Product 需要在 implementation 前更新 tech-plan 或新增 sprint。

## 10. 需要创建或更新的 sprint 文档

- 本轮已创建：`pre_start.md`、`prd.md`、`tech-plan.md`
- 本轮 closeout 已创建或更新：`tech-done.md`、`side2side_check.md`、`final.md`
