# Tech Plan - O3 Bounded Route Command Plan

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_08-09_o3_bounded_route_command_plan/`
- Product owner: `product-okr-owner`
- Planned implementation owner: `robot-algorithm-engineer`
- Implementation model: single owner closed loop
- Proof boundary: `software_proof_o3_o1_no_motion_bounded_route_command_plan_only`

## OKR 最低优先级核对

1. 当前 `OKR.md` 数字完成度最低的 Objective 是 O5，约 `85%`。
2. 本 sprint 不针对 O5，转向 O3/O1 controlled route execution 前置条件。
3. 不针对 O5 的具体理由：O5 当前缺真实公网 HTTPS/TLS、4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic、真实手机/browser 和 external production evidence；继续 local/mock readiness、cutover packet、handoff 或 support-only wrapper 会重复消费同一 blocker。
4. 不针对 O6/O7 的具体理由：06:05 已完成 same-task replay packet readback-only increment；继续 O6/O7 readback-only wrapper 不会靠近 route execution 缺口。
5. 本轮针对 O3/O1 的理由：07:07 gate record 明确下一步缺 `bounded route execution command plan with abort criteria`，这是当前本机可生成、可测试且不触发运动的最窄前置项。
6. 收口要求：若本轮仅生成 no-motion bounded plan，OKR 百分比不调整，KR `不归档`；但它应把下一轮 live execution 缺口收敛到 operator approval、current live HIL/stop path、同窗口 LiDAR/localization/TF 和 Nav2/controller result。

## 输入

- Gate record: `sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record/artifacts/algorithm/controlled_route_execution_gate_record.json`
- Source packet summary: `sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/artifacts/algorithm/same_task_replay_packet_summary.json`
- Source route CSV ref from gate: `sprints/2026.07.13_04-02_o3_28_pose_fixed_route_consumer/artifacts/algorithm/fixed_route_28_pose_route.csv`

Identity and count constants:

- `packet_id=packet_o3_28_pose_same_task_replay_7d57826142b0c79c`
- `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`
- `route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`
- `route_csv_row_count=28`
- `replay_jsonl_event_count=28`
- `packet_jsonl_event_count=28`
- `path_structured_pose_count=28`

Required false fields:

- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `safe_to_control=false`
- `robot_control_executed=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`

Required no-motion guards:

- no `/cmd_vel`
- no `/api/base/manual`
- no NavigateToPose
- no WAVE ROVER UART

## 技术方案

`robot-algorithm-engineer` 新增一个离线 helper：

- `onboard/scripts/o3_bounded_route_command_plan.py`

建议输出：

- `sprints/2026.07.13_08-09_o3_bounded_route_command_plan/artifacts/algorithm/bounded_route_command_plan.json`

建议 schema：

- `trashbot.o3.bounded_route_command_plan.v1`

核心逻辑：

1. 读取 07:07 `controlled_route_execution_gate_record.json`，确认 schema、identity、counts、false safety fields、no-motion guard 和 `controlled_route_execution_gate_status=fail_closed_input_packet_validated`。
2. 读取 gate record 中的 `route_csv_ref`，用 `csv.DictReader` 解析 28 个 pose row。不要依赖字符串截取。
3. 计算相邻 pose 的 segment distance、总距离、最大 segment distance、segment count。
4. 输出保守 speed/timeout caps，例如 `max_linear_speed_mps=0.10`、`max_angular_speed_radps=0.30`、`segment_timeout_s` 和 `route_timeout_s`。这些只是未来受控执行计划参数，不是实际控制命令。
5. 对每段输出或汇总 abort checks：operator stop、localization stale、LiDAR stale/no sample、TF missing、controller unavailable、route deviation over threshold、segment timeout、any safety/control flag true/missing。
6. 输出 fixed false fields 和 rejected claims，保持所有 success/control/HIL/delivery 字段 false。
7. 如果 gate record 或 route CSV 漂移，CLI 必须非零并输出 fail-closed error，不写 success-like artifact。

## 文件范围

允许 `robot-algorithm-engineer` 修改：

- `onboard/scripts/o3_bounded_route_command_plan.py`
- `onboard/tests/test_o3_bounded_route_command_plan.py`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.13_08-09_o3_bounded_route_command_plan/artifacts/algorithm/bounded_route_command_plan.json`
- `sprints/2026.07.13_08-09_o3_bounded_route_command_plan/tech-done.md`

不允许修改：

- `OKR.md`
- O6/O7 code or UI
- hardware driver or launch files
- production cloud config
- 07:07 gate source artifact 或 05:02 packet source artifact
- 范围外 sprint 目录

## 接口影响

- 只新增本地 Algorithm artifact contract。
- 不新增 ROS2 topic/action/service。
- 不调用 `/cmd_vel`、`/api/base/manual`、NavigateToPose、controller/BT 或 WAVE ROVER UART。
- 不改变 O6/O7 consumer API。
- 不改变 production cloud behavior。

## 验收命令

`robot-algorithm-engineer` 必须运行并在 `tech-done.md` 记录：

```bash
python3 -m py_compile onboard/scripts/o3_bounded_route_command_plan.py
python3 -m unittest onboard.tests.test_o3_bounded_route_command_plan
python3 onboard/scripts/o3_bounded_route_command_plan.py \
  --gate-record sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record/artifacts/algorithm/controlled_route_execution_gate_record.json \
  --output-dir sprints/2026.07.13_08-09_o3_bounded_route_command_plan/artifacts/algorithm
python3 -m json.tool sprints/2026.07.13_08-09_o3_bounded_route_command_plan/artifacts/algorithm/bounded_route_command_plan.json >/tmp/o3_bounded_route_command_plan.pretty.json
python3 - <<'PY'
import json
from pathlib import Path

path = Path("sprints/2026.07.13_08-09_o3_bounded_route_command_plan/artifacts/algorithm/bounded_route_command_plan.json")
data = json.loads(path.read_text())
assert data["schema"] == "trashbot.o3.bounded_route_command_plan.v1"
assert data["packet_id"] == "packet_o3_28_pose_same_task_replay_7d57826142b0c79c"
assert data["task_id"] == "task_o3_28_pose_fixed_route_consumer_20260713_0402"
assert data["route_intent_id"] == "route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path"
assert data["execution_plan_status"] == "blocked_pending_live_safety_gate"
assert data["segment_count"] == 27
assert data["route_csv_row_count"] == 28
assert data["route_execution_success"] is False
assert data["delivery_success"] is False
assert data["hil_pass"] is False
assert data["safe_to_control"] is False
assert data["robot_control_executed"] is False
assert data["publishes_cmd_vel"] is False
assert data["calls_base_manual"] is False
assert data["uses_base_uart"] is False
guards = " ".join(data["no_motion_control_guard"])
assert "no /cmd_vel" in guards
assert "no /api/base/manual" in guards
assert "no NavigateToPose" in guards
assert "no WAVE ROVER UART" in guards
print("bounded_route_command_plan_acceptance_ok")
PY
rg -n "bounded_route_command_plan|packet_o3_28_pose_same_task_replay_7d57826142b0c79c|blocked_pending_live_safety_gate|route_execution_success=false|safe_to_control=false|no /cmd_vel|no /api/base/manual|no NavigateToPose|no WAVE ROVER UART" \
  onboard/scripts/o3_bounded_route_command_plan.py \
  onboard/tests/test_o3_bounded_route_command_plan.py \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.13_08-09_o3_bounded_route_command_plan/tech-done.md \
  sprints/2026.07.13_08-09_o3_bounded_route_command_plan/artifacts/algorithm/bounded_route_command_plan.json
git diff --check -- \
  onboard/scripts/o3_bounded_route_command_plan.py \
  onboard/tests/test_o3_bounded_route_command_plan.py \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.13_08-09_o3_bounded_route_command_plan
```

## 验收标准

通过标准：

- artifact 可被 `json.tool` 解析。
- exact packet/task/route intent 与 07:07 gate record 一致。
- 28 pose 被解析为 27 segments，并输出总距离、最大 segment 距离和保守 command caps。
- abort criteria 清楚，且包含 operator stop、localization、LiDAR、TF、controller、route deviation、timeout、control permission false gate。
- 所有 success/control/HIL/delivery fields 固定 false。
- literal no-motion guards 可被 `rg` 找到。
- `tech-done.md` 记录实际改动、验证输出、失败定位和剩余风险。

不通过标准：

- 只写 prose checklist，没有机器可读 bounded plan。
- 新增或调用任何运动控制路径。
- 把 plan ready 写成 route execution success、delivery success、HIL pass 或 safe-to-control。
- 复写 07:07 gate source 或 05:02 packet source。
- 未同步 navigation 文档或未运行 targeted tests。

## 风险和回滚边界

- 本轮 artifact 仍是 no-motion software proof，不能提升为 live execution 证据。
- 若 route CSV 坐标字段格式漂移，helper 必须 fail closed 并说明具体字段。
- 回滚边界是新增 helper/test、sprint artifact 和 docs/navigation 的本轮小节。

## 后续收口要求

`side2side_check.md` 需要对照 PRD/tech-plan 验收。`final.md` 必须明确 Product 是否接受 bounded route command plan，以及不得声明的能力。`OKR.md` 只能在 Product 验收后由主节点/Product 更新，并且预计保持主百分比不调整。
