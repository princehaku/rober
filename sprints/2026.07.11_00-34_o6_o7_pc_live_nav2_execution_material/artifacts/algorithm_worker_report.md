# Algorithm Worker Report

## 1. 自主能力目标和本轮抓手

- 目标：把 2026-07-03 的 PC live Nav2 execution material 以安全 additive section 形式接入 `field_route_evidence_manifest.py`，供 O6/O7 后续 archive/readback/consumer 复用。
- 抓手：新增 `--pc-live-nav2-execution-material-json`，只消费短安全 JSON 字段，输出 `trashbot.pc_live_nav2_execution_material.v1`，同时写入 manifest 顶层和 `field_motion_evidence_packet.pc_live_nav2_execution_material`，并对 dangerous true / unsafe text fail-closed。

## 2. 改动文件和接口影响

- `onboard/scripts/field_route_evidence_manifest.py`
  - 新增 schema/proof scope/status 常量。
  - 新增 CLI 参数 `--pc-live-nav2-execution-material-json`。
  - 新增 JSON 读取、安全审计和 packet builder。
  - 新增 manifest 顶层与 `field_motion_evidence_packet` 同步写入。
- `onboard/tests/test_field_route_evidence_manifest.py`
  - 新增 source fixture helper。
  - 新增 ready / hostile fail-closed 两个回归测试。
- `docs/navigation/field_route_evidence_manifest.md`
  - 新增 CLI、packet contract、ready 条件、输出字段和 fail-closed 边界。
- `sprints/2026.07.11_00-34_o6_o7_pc_live_nav2_execution_material/artifacts/pc_live_nav2_execution_material_source.json`
  - 新增短安全 source material，来源说明指向 `sprints/2026.07.03_20-46_pc_nav2_o11_tail_wasd_back_alias/tech-done.md`。

## 3. 实现内容

- 接口合同：
  - 输出 schema：`trashbot.pc_live_nav2_execution_material.v1`
  - proof scope / evidence boundary：`software_proof_pc_live_nav2_execution_material_only`
  - ready status：`pc_live_nav2_execution_material_ready_not_delivery_proof`
  - blocked status：`blocked_not_proven`
- 安全边界：
  - 顶层固定 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`route_execution_success=false`、`hil_pass=false`。
  - 输入里的 `robot_control_executed=true` 仅作为 `source_robot_control_executed` 摘要事实保留，不提升 manifest 顶层控制字段。
  - 对 `delivery_success=true`、`safe_to_control=true`、`primary_actions_enabled=true`、`route_execution_success=true`、`hil_pass=true`，以及 URL、token、raw log、traceback、base64、绝对路径做 section-local fail-closed。
- 保留的安全摘要：
  - `source_sprint`、`source_doc`、`verified_at`
  - `nav2_goal_accepted`、`cancel_accepted`
  - `uses_base_uart`
  - `base_command_nonzero_observed`、`base_command_nonzero_count`
  - `base_feedback_sample_count`
  - `base_feedback_lr_nonzero_proven=false`
  - `base_feedback_imu_attitude_delta_observed`
  - `motion_signal_observed`
  - `nav2_terminal_status`
  - `next_required_evidence`

## 4. 测试、dry-run 或上车验证结果

### 验收命令

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py
```

- 结果：通过，无输出。

```bash
python3 -m unittest onboard.tests.test_field_route_evidence_manifest
```

- 结果：通过。
- 关键日志：

```text
Ran 77 tests in 0.581s

OK
```

```bash
git diff --check -- onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py docs/navigation/field_route_evidence_manifest.md sprints/2026.07.11_00-34_o6_o7_pc_live_nav2_execution_material
```

- 结果：通过，无输出。

## 5. 数据、样本或调试输出变化

- 新增 source material：
  - `sprints/2026.07.11_00-34_o6_o7_pc_live_nav2_execution_material/artifacts/pc_live_nav2_execution_material_source.json`
- 新增 manifest additive section：
  - 顶层：`pc_live_nav2_execution_material`
  - nested：`field_motion_evidence_packet.pc_live_nav2_execution_material`
- ready 样本保留的核心事实：
  - `goal_accepted=true`
  - `uses_base_uart=true`
  - `base_command_nonzero_observed=true`
  - `base_command_nonzero_count=733`
  - `base_feedback_sample_count=5941`
  - `base_feedback_lr_nonzero_proven=false`
  - `base_feedback_imu_attitude_delta_observed=true`
  - `motion_signal_observed=true`
  - `goal_result_status=goal_timeout_cancel_requested`
  - `result_status=goal_timeout_cancel_requested`
  - `nav2_terminal_status=goal_timeout_cancel_requested`

## 6. 失败定位

- 无。本轮验收命令均一次通过。

## 7. 剩余风险和下一步能力建设建议

- 当前 additive 只证明历史 PC live Nav2 执行摘要已被安全消费，不证明当前 same-run live route execution、delivery success、operator acceptance 或 HIL 通过。
- `base_feedback_lr_nonzero_proven` 仍固定为 false，这正是本合同要保留的 fail-closed 边界；后续若要提升 same-task mission 材料质量，优先接入当前 live wheel L/R nonzero feedback 和 same-run route execution success 材料。
- 本轮未执行真实 Nav2、硬件或上车命令，证据边界仍是 `software_proof_pc_live_nav2_execution_material_only`。

## 8. 返工记录

- 验收发现 O6/O7 消费 canonical 字段使用 `goal_accepted` 与 `goal_result_status`，而 producer 首版只输出了 alias `nav2_goal_accepted` 与 `nav2_terminal_status`。
- 本次返工已在 `pc_live_nav2_execution_material` 顶层补齐 canonical：
  - `goal_accepted`
  - `goal_result_status`
  - `result_status`
- 兼容 alias 仍保留：
  - `nav2_goal_accepted`
  - `nav2_terminal_status`
- source material `pc_live_nav2_execution_material_source.json` 已补齐 `goal_result_status`，并保留 `terminal_status` alias。
- 测试与文档已同步改为 canonical + alias 双写说明。

### 返工复验

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py
python3 -m unittest onboard.tests.test_field_route_evidence_manifest
git diff --check -- onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py docs/navigation/field_route_evidence_manifest.md sprints/2026.07.11_00-34_o6_o7_pc_live_nav2_execution_material
```

- 结果：返工后复验通过。
