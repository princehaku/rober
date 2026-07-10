# O7 Worker Report - field operator confirmation material

完成时间：2026-07-10 15:54:06 CST

## 用户旅程变化和触点收益

- O7 consumer detail 默认 include 新增 `field_operator_confirmation_material`，operator 打开同一 task detail 时可以直接看到现场 operator report / confirmation 材料是否存在，而不需要回看 O6 原始 JSON。
- UI 在 O7 fixture preview / consumer detail 区域新增只读 `Field operator confirmation material` 摘要，展示 `status`、`proof_scope`、`source_origin`、operator report/confirmation present 与 status、安全预检布尔位、same-task consumed、linked route/delivery material、material summaries、blocked reasons、next required evidence 和固定 false fields。
- 该入口不新增控制按钮，不把 operator 材料解释为真实送达、真实路线执行、HIL 通过或可控状态。

## 实际改动文件

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/App.test.ts`
- `pc-tools/workstation/test/catalog.test.ts`
- `docs/interfaces/o7_realtime_operator_console.md`
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.07.10_15-22_o6_o7_field_operator_confirmation_material/artifacts/o7_worker_report.md`

## 接口影响

- 新增 O7 schema：`trashbot.pc_tools_workstation.o7_field_operator_confirmation_material.v1`。
- O7 consumer detail 默认 include 新增 `field_operator_confirmation_material`。
- adapter 从 O6 top-level、`field_evidence`、`field_motion_evidence_packet`、`artifact_bundle`、`artifact_bundle_consumer_ingest`、`artifact_bundle_readiness` 归一读取 field operator material。
- ready status 固定为 `field_operator_confirmation_material_ready_not_delivery_proof`，proof scope 固定为 `software_proof_field_operator_confirmation_material_only`。
- 缺字段、task mismatch、dangerous true、unsafe text/list、proof scope mismatch 均 fail-closed。
- 固定 false：`delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`route_execution_success=false`、`hil_pass=false`、`connects_cloud_production=false`。

## 前后端 / ROS2 联调结果

- 本轮只消费 O6 consumer read HTTP detail 的软件证据链，没有连接 ROS2 graph、真实云、真实串口或 WAVE ROVER。
- 前端 UI 与 Node adapter 已通过 mock O6 consumer detail fixtures 覆盖 ready、default include、readiness 汇总和 fail-closed 场景。
- 证据边界：`software_proof_field_operator_confirmation_material_only`，不等于真实 operator 现场签收、真实 delivery success、真实 route execution 或 HIL。

## 验证命令输出

```text
$ cd pc-tools/workstation && npm run test && npm run build && npm run lint
Test Files  3 passed (3)
Tests  487 passed (487)
vite v7.3.3 building client environment for production...
✓ 34 modules transformed.
✓ built in 1.81s
> rober-pc-tools-workstation@0.1.0 lint
> eslint .
```

```text
$ git diff --check -- pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/App.test.ts pc-tools/workstation/test/catalog.test.ts docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md sprints/2026.07.10_15-22_o6_o7_field_operator_confirmation_material
# no output, passed
```

## 失败定位与修复

- 初次 `npm run test` 发现一个 catalog expectation 仍使用旧 default include list，已补入 `field_operator_confirmation_material`。
- 初次 combined acceptance 中 `npm run build` 发现 `failClosedDetail` 调用 `blockedArtifactBundleReadiness` 时漏传 field operator material 参数，导致 checklist 被传到 field operator 参数位；已补齐 blocked field operator summary。
- 同次 build 发现两个 fixture 在 `...PROOF_FLAGS` 前后重复声明 `delivery_success`、`safe_to_control`、`primary_actions_enabled`，已改为先 spread proof flags，再显式覆盖固定 false 字段。

## 剩余风险

- 本轮验证是 workstation + O6 mock/fixture 软件证明，不包含真实 O6 production relay、真实 operator 现场报告、真实 ROS2/Nav2、真实底盘运动或 HIL。
- 如果 Algorithm/O6 后续调整 `field_operator_confirmation_material` 的字段名、status、proof scope 或 material summary shape，需要同步更新 O7 adapter fail-closed allowlist 和 UI 展示。
- 当前 UI 只读展示材料状态；任何 Start/Cancel/Confirm/Manual control 仍必须走既有安全入口，不能从该 section 推导可控。
