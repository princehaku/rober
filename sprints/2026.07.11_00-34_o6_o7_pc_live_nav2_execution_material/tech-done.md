# O6/O7 PC Live Nav2 Execution Material Tech Done

## sprint_type

sprint_type: epic

## 实际改动

- Algorithm worker 在 `field_route_evidence_manifest.py` 新增 `--pc-live-nav2-execution-material-json`，输出 `trashbot.pc_live_nav2_execution_material.v1`，并同时写入 manifest 顶层与 `field_motion_evidence_packet.pc_live_nav2_execution_material`。
- O6 worker 在 `remote_cloud_relay.py` 新增 `pc_live_nav2_execution_material` 的 archive/readback/include 合同，输出 `trashbot.o6.pc_live_nav2_execution_material.v1`，并对 bad schema、bad proof scope、task mismatch、unsafe text、`base_feedback_lr_nonzero_proven=true` 做 section-local fail-closed。
- O7 worker 在 workstation 默认 include/consume/display `pc_live_nav2_execution_material`，展示 `source_sprint`、`goal_accepted`、UART/base command/IMU 摘要、`base_feedback_lr_nonzero_proven=false` 与 remaining evidence，不新增动作按钮，也不放宽 success / control false 字段。
- 集成验收 worker 新增 `artifacts/integration_acceptance_report.md`，复核 Algorithm -> O6 -> O7 对 `goal_accepted`、`goal_result_status`、`result_status`、`nav2_terminal_status` 的 canonical/legacy 字段兼容顺序。

## 与计划的偏差

- 无范围外扩。实际交付仍限定在 prior live material intake、archive/readback 和 O7 只读消费。
- 中途发生一次字段漂移返工：Algorithm 首版只写 alias，O6 首版只输出 `result_status`，O7 初版默认读取顺序也偏旧。返工后统一改为 canonical 优先、legacy 兼容。

## 验证结果

### Algorithm worker

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py
python3 -m unittest onboard.tests.test_field_route_evidence_manifest
git diff --check -- onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py docs/navigation/field_route_evidence_manifest.md sprints/2026.07.11_00-34_o6_o7_pc_live_nav2_execution_material
```

- 结果：通过。
- 关键输出：

```text
Ran 77 tests in 0.578s

OK
```

### O6 worker

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md sprints/2026.07.11_00-34_o6_o7_pc_live_nav2_execution_material
```

- 结果：通过。
- 关键输出：

```text
Ran 183 tests in 79.196s

OK
```

### O7 worker

```bash
cd pc-tools/workstation && npm run test && npm run build && npm run lint
git diff --check -- pc-tools/workstation docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md sprints/2026.07.11_00-34_o6_o7_pc_live_nav2_execution_material
```

- 结果：通过。
- 关键输出：

```text
Tests 490 passed (490)
vite build + tsc passed
eslint . passed
```

### 集成验收

```bash
python3 -m unittest onboard.tests.test_field_route_evidence_manifest.FieldRouteEvidenceManifestTest.test_pc_live_nav2_execution_material_ready_consumes_safe_short_summary
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay.RemoteCloudRelayHttpTest.test_o6_pc_live_nav2_execution_material_in_field_and_bundle_readback
cd pc-tools/workstation && npm run test -- -t "keeps pc live Nav2 execution material ready"
```

- 结果：通过。
- 关键输出：

```text
Ran 1 test in 0.008s OK
Ran 1 test in 0.789s OK
Tests 1 passed | 489 skipped (490)
```

## OKR 影响

- 本轮允许把 O6 从约 `~92%` 保守上调到约 `~93%`：理由是 O6 新消费了一类此前未进入 O6 archive/readback 的 prior live Nav2 execution material，并完成 canonical/legacy 字段漂移修平。
- 本轮允许把 O7 从约 `~92%` 保守上调到约 `~93%`：理由是 O7 默认消费/展示了同一 `task_id` 的 PC live Nav2 execution material，operator 可以在只读面板中直接看到“已到 Nav2/UART/base-command/IMU 事实，但仍未到 wheel L/R nonzero、delivery 或 HIL”的边界。
- O5 维持约 `~85%`：本轮没有新增真实 production external evidence，不能靠 wrapper/contract/support-only lane 继续涨分。
- O1 维持约 `~92%`：最近两轮已连续卡在 current same-run HIL / wheel L/R / external video / LiDAR motion delta blocker，本轮未新增该链路的 live/hil 外部材料。

## 剩余风险

- 证据边界仍是 `software_proof_pc_live_nav2_execution_material_only`，不证明 current live rerun、route execution success、delivery success、operator acceptance、HIL pass 或 production cloud。
- `base_feedback_lr_nonzero_proven=false` 仍是这轮最关键的 fail-closed 边界，不能把 base command nonzero 和 IMU attitude delta 解释成真实底盘轮速闭环已证明。
- 本轮消费的是 `2026-07-03` 既有 PC live Nav2 execution material，不是 2026-07-11 当天重新上车执行。
