# O7 Worker Report - route_bag_evidence read-only intake

Run time: 2026-07-09 17:30:23 CST
Role: full-stack-software-engineer

## Scope

- 在 O7 consumer read adapter 中请求并读取 `route_bag_evidence`。
- 在 shared contracts 与 O7 fixture preview UI 中展示 route bag source/status、topic/message/timestamp 摘要、blocked reasons、next evidence 与固定 false safety fields。
- 将 `route_bag_evidence` 汇总进 `artifact_bundle_readiness`，保持只读，不新增 submit/control/action。
- 文档与 Vitest 覆盖同步更新。

## Files changed

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.07.09_17-00_o6_o7_route_bag_evidence_intake/artifacts/o7_worker_report.md`

## Implementation notes

- `route_bag_evidence` 只接受 `trashbot.route_bag_evidence.v1` / `trashbot.o6.route_bag_evidence.v1` 与 `proof_scope=software_proof_route_bag_evidence_intake_only`。
- 展示范围限制为脱敏摘要：`source_label`、metadata/db3 状态、topic/message count、首末 timestamp、限量 topic 名称、blocked reasons 与 next required evidence。
- fail-closed 覆盖 schema mismatch、proof scope mismatch、危险 true 字段、unsafe text、URL、绝对路径、base64、raw/path/root、credential URL、串口路径、完整 DB3 内容与 `/cmd_vel` topic。
- 安全 flags 固定 false：`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`route_execution_success=false`、`live_nav2_run_connected=false`。

## Validation

- `cd pc-tools/workstation && npm run test && npm run build && npm run lint` passed:
  - `Test Files  3 passed (3)`
  - `Tests  479 passed (479)`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - `✓ built in 1.72s`
  - Vite reported the existing large-chunk warning only; no build error.
  - `eslint .`
- `rg -n "route_bag_evidence|software_proof_route_bag_evidence_intake_only|safe_to_control|delivery_success" ...` passed and matched the adapter, contracts, UI, tests, docs and this worker report.
- `git diff --check -- ...` passed with no whitespace errors.

## Remaining risks

- 当前结论是 `software_proof_route_bag_evidence_intake_only`，只证明 PC/O7 可消费脱敏 route bag 摘要；不证明真实 DB3 完整内容、真实 route execution、真实 Nav2 live run、真实机器人运动或真实 delivery success。
