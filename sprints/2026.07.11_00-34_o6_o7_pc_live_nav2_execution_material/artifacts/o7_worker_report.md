# O7 Worker Report

## 用户旅程变化和触点收益

- O7 consumer detail / fixture preview 现在默认消费 `pc_live_nav2_execution_material`，operator 不需要翻 sprint 文档或原始日志，就能在同一只读面板里看到 `source_sprint`、`goal_accepted`、UART/base command/IMU 事实、wheel L/R 仍未证明以及下一步缺什么证据。
- 这个 summary block 保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`，所以 UI 不会把 live Nav2 摘要误渲染成可发车或已成功。
- `artifact_bundle_readiness` 主路径也带上了该 section，方便 O7 operator 在 bundle / mission material / localization 等既有摘要旁边一起复核。

## 实际改动文件

- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
- `docs/interfaces/o7_realtime_operator_console.md`
- `docs/product/pc_tools_workstation.md`

## 接口影响

- O7 默认 detail include 新增 `pc_live_nav2_execution_material`。
- O7 新增只读消费合同：`trashbot.pc_tools_workstation.o7_pc_live_nav2_execution_material.v1`。
- `artifact_bundle` / `artifact_bundle_consumer_ingest` / `artifact_bundle_readiness` / `consumer_task_detail` 都增加了 `pc_live_nav2_execution_material` 字段。

## 前后端 / ROS2 联调结果

- 本轮没有真实 ROS2 或机器人运行时联调；使用 O6-shaped fixture 覆盖 direct、artifact bundle readiness 等现有消费路径。
- 现有 O7 adapter 已兼容从 top-level、`field_evidence`、`field_motion_evidence_packet`、`artifact_bundle`、`artifact_bundle_consumer_ingest`、`artifact_bundle_readiness` 读取该 section。

## 验证命令输出结果

```bash
cd pc-tools/workstation && npm run test
# Test Files  3 passed (3)
# Tests  489 passed (489)

cd pc-tools/workstation && npm run build
# vite build + tsc passed
# 仅保留既有 chunk size warning

cd pc-tools/workstation && npm run lint
# eslint . passed

git diff --check -- pc-tools/workstation docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md sprints/2026.07.11_00-34_o6_o7_pc_live_nav2_execution_material
# no output
```

## 失败定位

- 首轮 `npm run build` 前，`blockedArtifactBundleReadiness()` 的新参数顺序漏传 `pc_live_nav2_execution_material`，导致 TypeScript 把 `localization_path_material_readback` 误传给新 summary 类型；已修正。
- 首轮 `npm run test` 有一处 `catalog.test.ts` 的默认 include 断言未同步新增 section；已补齐。

## 剩余风险

- 当前仍是 `software_proof_pc_live_nav2_execution_material_only`；不证明真实 live route execution、真实 delivery success、真实 wheel L/R 非零或真实 safe-to-control。
- O7 侧已按 fail-closed 展示，但后续还需要 O6/Algorithm 产出的最终 payload 与本次假设字段名保持一致，尤其是 `goal_result_status`、`base_feedback_*` 和 `next_required_evidence`。

## 返工记录

- 2026-07-11 本轮按验收漂移返工：`pc_live_nav2_execution_material` 的 `goal_result_status` 现优先读取 canonical `goal_result_status`，并兼容 `result_status`、`nav2_terminal_status`、`terminal_status`；`goal_accepted` 现优先读取 canonical `goal_accepted`，并兼容 `nav2_goal_accepted`。
- 新增测试覆盖三类输入不被误判 blocked：O6 canonical top-level payload、Algorithm canonical `field_motion_evidence_packet.pc_live_nav2_execution_material`、Algorithm legacy alias payload。
- UI summary 维持只读展示 `goal_result_status=...`，不新增控制按钮，也不放宽任何 success / safe-to-control false 字段。

### 返工改动文件

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/test/catalog.test.ts`
- `docs/interfaces/o7_realtime_operator_console.md`
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.07.11_00-34_o6_o7_pc_live_nav2_execution_material/artifacts/o7_worker_report.md`

### 返工验收命令输出

```bash
cd pc-tools/workstation && npm run test && npm run build && npm run lint
# Test Files  3 passed (3)
# Tests  490 passed (490)
# vite build + tsc passed
# eslint . passed

git diff --check -- pc-tools/workstation docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md sprints/2026.07.11_00-34_o6_o7_pc_live_nav2_execution_material
# no output
```
