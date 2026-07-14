# Tech Plan - O3 Controlled Route Execution Gate Record

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record/`
- Product owner: `product-okr-owner`
- Planned implementation owner: `robot-algorithm-engineer`
- Implementation model: single owner closed loop
- Proof boundary: `software_proof_o3_o1_fail_closed_controlled_route_execution_gate_record_only`

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节数字完成度最低的 Objective 是 O5，约 `85%`。
2. 本 sprint 不针对 O5，转向 O3/O1 route execution 前 gate。O1 约 `94%`，O6/O7 约 `93%`，O3 是当前临时激活的现场验证 lane。
3. 不针对 O5 的具体理由：O5 当前缺真实公网/生产 external evidence，包括真实公网 HTTPS/TLS、4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic、真实手机/browser 验收。最近多轮已经确认 O5 readiness、checklist、handoff、cutover packet 或 support-only wrapper 不会产生新的 external evidence，继续推进会重复消费同一 blocker。
4. 不针对 O6/O7 的具体理由：06:05 已完成 same-task replay packet readback-only increment；继续 O6/O7 readback-only wrapper 会重复消费 readback 边界，不会靠近当前 route execution 缺口。
5. 选择 O3/O1 gate 的理由：05:02 已有 accepted `packet_id=packet_o3_28_pose_same_task_replay_7d57826142b0c79c`、`task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`、`route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path` 和 28/28/28 counts，下一步应该验证它能否作为受控 route execution 前输入候选，并 fail closed 产出 gate record。
6. 收口要求：若本轮只做 fail-closed gate，OKR 百分比大概率不调整，KR `不归档`；但该 sprint 合法价值是避免重复旧 wrapper，并把下一步收敛到真实执行准入和 next live command gate。

## 输入证据

权威输入：

- Source summary: `sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/artifacts/algorithm/same_task_replay_packet_summary.json`
- Product closeout: `sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/final.md`
- O6/O7 readback closeout: `sprints/2026.07.13_06-05_o6_o7_same_task_replay_packet_readback/final.md`

必须保留的 identity：

- `packet_id=packet_o3_28_pose_same_task_replay_7d57826142b0c79c`
- `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`
- `route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`
- `same_task_identity_verified=true`
- `same_task_replay_packet_ready=true`

必须保留的 counts：

- `route_csv_row_count=28`
- `replay_jsonl_event_count=28`
- `path_structured_pose_count=28`

必须保留的 source hashes：

- `summary_sha256=9948414e1a46b6e78de5503a06d634e24c5e96aff38c1f4c7d756bd20eb0dc93`
- `route_csv_sha256=61b4020c93f01e595df4608e8b42545ce1b1d04eaff8798db55b0dda2aae7601`
- `replay_jsonl_sha256=530941a7ecb4768f6583cda4abca0d9bc92715ea0266fc96e83d3a860a0400b5`

必须固定 false fields：

- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `safe_to_control=false`
- `robot_control_executed=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`

## 技术方案

### Gate record artifact

后续 `robot-algorithm-engineer` 应新增或复用 Algorithm artifact 生成路径，输出机器可读 gate record。建议文件名：

- `artifacts/algorithm/controlled_route_execution_gate_record.json`

建议 schema：

- `trashbot.o3.controlled_route_execution_gate_record.v1`

建议 top-level fields：

- `schema`
- `artifact_boundary`
- `generated_at_utc`
- `packet_id`
- `task_id`
- `route_intent_id`
- `source_summary_ref`
- `packet_jsonl_ref`
- `route_csv_ref`
- `route_csv_row_count`
- `replay_jsonl_event_count`
- `path_structured_pose_count`
- `source_fingerprints`
- `identity_validation_status`
- `count_validation_status`
- `source_hash_validation_status`
- `controlled_route_execution_gate_status`
- `dry_run_execution_readiness_status`
- `next_live_command_gate`
- `missing_live_execution_prerequisites`
- `blocked_reasons`
- `rejected_claims`
- `route_execution_success`
- `delivery_success`
- `hil_pass`
- `safe_to_control`
- `robot_control_executed`
- `publishes_cmd_vel`
- `calls_base_manual`
- `uses_base_uart`

### Gate semantics

Gate status must be fail-closed:

- If identity/count/hash validation passes, status may be `blocked_ready_for_manual_safety_review` or `fail_closed_input_packet_validated`.
- If any identity/count/hash check fails, status must be `blocked_source_packet_mismatch`.
- In both cases, `safe_to_control=false` and `robot_control_executed=false` remain fixed.
- The artifact must never output a success-like route execution status.

### No-motion guard

The implementation must not run route execution commands. It must not publish to control topics or call control APIs. The record and tests must include literal guard anchors:

- no /cmd_vel
- no /api/base/manual
- no NavigateToPose
- no WAVE ROVER UART

The implementation must not call ROS2 action execution, Nav2 controller/BT, `/api/base/manual`, WAVE ROVER UART, keyboard/manual drive, or any endpoint that can move the robot.

### Next live command gate

`next_live_command_gate` must list the evidence required before a future controlled route execution sprint can flip any control/success boolean:

- explicit safety operator approval or equivalent recorded safety gate
- current live HIL / stop path / controlled environment material
- bounded route execution command plan with abort criteria
- LiDAR/localization/TF readiness in the same live window
- Nav2/controller execution result, not only planner path proof
- delivery/operator acceptance evidence before `delivery_success` can change

## 后续 Algorithm owner 文件范围

建议允许后续 `robot-algorithm-engineer` 修改：

- `sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record/artifacts/algorithm/controlled_route_execution_gate_record.json`
- `sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record/tech-done.md`
- Algorithm helper/test files only if needed to generate and validate the artifact, with exact paths listed in `tech-done.md`

默认不允许修改：

- O6/O7 code or UI
- hardware driver or launch files
- production cloud config
- `OKR.md`
- docs outside this sprint unless implementation changes product/interface behavior and the future owner is explicitly allowed to sync docs

## 接口影响

- 本 planning sprint 无代码接口影响。
- 后续 implementation 只新增 Algorithm artifact contract。
- 不新增 ROS2 topic/action/service。
- 不新增 `/cmd_vel`、`/api/base/manual`、NavigateToPose、controller/BT 或 WAVE ROVER UART 调用。
- 不改变 O6/O7 consumer API。
- 不改变 production cloud behavior。

## 验收命令

Product planning 本轮必须运行：

```bash
git diff --check -- sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record
rg -n "sprint_type: epic|OKR 最低优先级核对|packet_o3_28_pose_same_task_replay_7d57826142b0c79c|task_o3_28_pose_fixed_route_consumer_20260713_0402|route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path|robot-algorithm-engineer|route_execution_success=false|safe_to_control=false|no /cmd_vel|no /api/base/manual" sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record
```

后续 `robot-algorithm-engineer` 必须运行并记录实际验证命令。最低建议：

```bash
python3 -m json.tool sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record/artifacts/algorithm/controlled_route_execution_gate_record.json
python3 - <<'PY'
import json
from pathlib import Path

path = Path("sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record/artifacts/algorithm/controlled_route_execution_gate_record.json")
data = json.loads(path.read_text())
assert data["packet_id"] == "packet_o3_28_pose_same_task_replay_7d57826142b0c79c"
assert data["task_id"] == "task_o3_28_pose_fixed_route_consumer_20260713_0402"
assert data["route_intent_id"] == "route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path"
assert data["route_csv_row_count"] == 28
assert data["replay_jsonl_event_count"] == 28
assert data["path_structured_pose_count"] == 28
assert data["route_execution_success"] is False
assert data["delivery_success"] is False
assert data["hil_pass"] is False
assert data["safe_to_control"] is False
assert data["robot_control_executed"] is False
assert data["publishes_cmd_vel"] is False
assert data["calls_base_manual"] is False
assert data["uses_base_uart"] is False
print("controlled_route_execution_gate_record_acceptance_ok")
PY
git diff --check -- sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record
```

If the future owner creates generator or unit-test code, they must also run the targeted test suite for those files and record command output in `tech-done.md`.

## 验收标准

通过标准：

- `controlled_route_execution_gate_record` 存在并可用 `json.tool` 解析。
- exact `packet_id`、`task_id`、`route_intent_id` 与 05:02 source 完全一致。
- 28/28/28 counts 与 05:02 source 完全一致。
- source hashes 或 hash prefixes 被结构化读回并用于断言。
- `next_live_command_gate` 明确真实执行缺口。
- `route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`、`robot_control_executed=false` 固定 false。
- artifact 明确 no /cmd_vel、no /api/base/manual、no NavigateToPose、no WAVE ROVER UART。
- Sprint `tech-done.md` 记录实际改动、验证输出、失败定位和剩余风险。

不通过标准：

- 只生成 checklist、handoff、readiness prose 或 route-intent wrapper，没有机器可读 gate record。
- 新增或调用任何控制路径。
- 把 packet ready 写成 route execution success、delivery success、HIL pass 或 safe-to-control。
- identity/count/hash 与 05:02 source 不一致但仍输出 ready-like 状态。
- 没有 tests 或 structured assertions 覆盖固定 false fields。

## 风险和回滚边界

- 本 sprint 只规划，不改代码；回滚边界是删除本 sprint 规划目录。
- 后续 Algorithm artifact 应是 additive evidence，不应影响已有 05:02 packet 或 06:05 readback。
- 若 source packet 缺失或 hash mismatch，后续 owner 应 fail closed，不能重写 source packet 来制造通过。
- 如果后续需要真实硬件准入，必须另开 Hardware/Algorithm 边界明确的 sprint，并重新查阅 `docs/vendor/VENDOR_INDEX.md`。

## 后续收口要求

`tech-done.md` 必须包含：

- `sprint_type: epic`
- 实际改动文件列表
- gate record artifact path
- identity/count/hash verification result
- no-motion guard evidence
- 验收命令输出片段
- 失败定位和修复记录
- 剩余风险
- OKR 影响判断：若仍只是 fail-closed gate，主百分比大概率不调整，KR `不归档`

`side2side_check.md` 必须对照本 PRD 和 tech-plan 做验收。`final.md` 必须明确 Product 是否接受 dry-run execution readiness record，以及不得声明的能力。
