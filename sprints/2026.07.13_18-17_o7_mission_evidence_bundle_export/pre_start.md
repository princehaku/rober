# Pre-start - O7 Mission Evidence Bundle Export

- sprint_type: epic
- sprint_status: planning
- started_at: 2026-07-13 18:17 CST
- owner: full-stack-software-engineer
- product_owner: product-okr-owner
- target_objectives: Objective 7 / Objective 6
- blocked_lowest_objective: Objective 5

## 上轮未完成项和本轮入口

最近闭环 sprint `sprints/2026.07.13_17-17_o7_delivery_result_intake/` 已把 O7 selected-task delivery result intake 接到 O6 `field-evidence` local/mock 写入路径，但仍只是单点 action-write receipt。

当前最低 Objective 是 O5，约 `85%`。最近 O5 sprint `sprints/2026.07.13_13-13_o5_cdn_tls_external_evidence_probe/` 已收口为 `blocked_http_status_not_success_class`，没有新的 success-class public endpoint、production DB/queue、OSS/CDN、4G/SIM 或真实 phone/browser 证据。本轮继续 O5 会重复消费同一外部 blocker。

O1/O3 下一步需要 explicit operator approval、current live `/api/base/stop`、UART zero-stop frame、`T=1001` L/R 归零、同窗口 LiDAR/localization/TF readiness 和 Nav2/controller result。当前自动化没有 operator approval，不能触碰真实运动、`/cmd_vel`、`/api/base/manual`、NavigateToPose 或 WAVE ROVER UART。

## 本轮目标

在不声明真实送达、真实路线执行或生产云的前提下，给 O7/O6 增加 selected-task mission evidence bundle export：

- O7 PC adapter 从 O6 consumer detail 读取同一 `task_id` 的 route/material/readiness、events、field evidence、same-task replay packet、delivery result/readiness 等只读材料。
- 返回一个 fail-closed local/mock evidence bundle export receipt，固定 false safety fields。
- 让 operator/reviewer 能把当前 selected task 的 mission evidence 一次性带走做审计、回放或后续训练材料归档。

## Owner 和边界

主责 owner：`full-stack-software-engineer`。

允许改动范围：

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/server/index.ts`
- `pc-tools/workstation/src/client/workstationApi.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/App.test.ts`
- `pc-tools/workstation/test/catalog.test.ts`
- `docs/interfaces/o7_realtime_operator_console.md`
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.07.13_18-17_o7_mission_evidence_bundle_export/tech-done.md`

范围外不得改动，尤其不得修改真实硬件配置、ROS2 launch、WAVE ROVER UART、`/cmd_vel`、`/api/base/manual`、NavigateToPose 或生产云凭证。

## 验收口径

接受为：

- `software_proof_o7_o6_mission_evidence_bundle_export_only`
- selected-task local/mock evidence bundle export
- O7/O6 task evidence aggregation/readback/export receipt

拒绝为：

- production cloud proof
- real cloud DB/queue/OSS/CDN proof
- route execution success
- delivery success
- operator acceptance
- HIL pass
- safe-to-control
- real phone/browser proof
- real dataset export

## 风险

- 如果 bundle 只重复 detail readback 而没有形成新的 selected-task export receipt，本轮不应接受。
- 如果 bundle 透传原始路径、URL、credential、base64/raw payload 或任何 dangerous true claim，必须 fail closed。
- 如果 UI 文案把 local/mock export 说成真实送达、生产云或 HIL，需要返工。
