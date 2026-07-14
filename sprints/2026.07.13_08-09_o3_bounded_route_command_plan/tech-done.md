# Tech Done - O3 Bounded Route Command Plan

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_08-09_o3_bounded_route_command_plan/`
- Owner: `robot-algorithm-engineer`
- Proof boundary: `software_proof_o3_o1_no_motion_bounded_route_command_plan_only`
- Artifact: `sprints/2026.07.13_08-09_o3_bounded_route_command_plan/artifacts/algorithm/bounded_route_command_plan.json`

## 自主能力目标和本轮抓手

本轮目标不是发车，而是基于 07:07 accepted `controlled_route_execution_gate_record.json`，补齐下一步 live execution 前置项之一：bounded route execution command plan with abort criteria。抓手是复核同一 `packet_id=packet_o3_28_pose_same_task_replay_7d57826142b0c79c`、`task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`、`route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`，并把 28 行 route CSV 解析为 27 个 segment 的 no-motion bounded plan。

本轮保持 strict no-motion/control guard：no /cmd_vel、no /api/base/manual、no NavigateToPose、no WAVE ROVER UART。未调用 ROS2 action、controller/BT、manual base、UART 或任何机器人运动命令。

## 实际改动文件和接口影响

- `onboard/scripts/o3_bounded_route_command_plan.py`
- `onboard/tests/test_o3_bounded_route_command_plan.py`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.13_08-09_o3_bounded_route_command_plan/artifacts/algorithm/bounded_route_command_plan.json`
- `sprints/2026.07.13_08-09_o3_bounded_route_command_plan/tech-done.md`

接口影响：只新增本地 Algorithm artifact contract `trashbot.o3.bounded_route_command_plan.v1`，不新增 ROS2 topic/action/service，不改变 hardware driver、launch、O6/O7 consumer API、production cloud 或 `OKR.md`。

## 实现内容

新增 `o3_bounded_route_command_plan.py`，只读取 07:07 gate record 和其 `route_csv_ref` 指向的 04:02 route CSV。生成器会在写出前执行：

- gate record 校验：schema、`controlled_route_execution_gate_status=fail_closed_input_packet_validated`、identity、28/28/28 counts、source validation statuses、literal no-motion guards 必须匹配；
- safety 校验：`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`、`robot_control_executed=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`uses_base_uart=false` 必须显式为 false；
- route CSV 校验：使用 `csv.DictReader` 解析，不做字符串截取；每行 `route_intent_id`、`task_id`、`order` 和 `strict_no_motion=True` 必须匹配；
- segment 计划：28 行 route CSV 生成 27 个 segment，输出保守 caps、segment distance summary、per-segment abort checks 和 global abort criteria；
- fail-closed guard：gate 或 CSV 任一漂移时抛出 `PlanInputError`，CLI 返回非零 `blocked_bounded_route_command_plan_input_mismatch`，不会生成 success-like artifact。

新增单测覆盖有效输入、literal guard 缺失、route CSV 计数漂移和 `safe_to_control=true` 漂移。导航文档追加 08:09 bounded plan 合同，明确该 artifact 不能被升级为 route execution、delivery、HIL 或 safe-to-control。

## Bounded Plan 结果

生成的 artifact 关键字段：

- `schema=trashbot.o3.bounded_route_command_plan.v1`
- `proof_boundary=software_proof_o3_o1_no_motion_bounded_route_command_plan_only`
- `execution_plan_status=blocked_pending_live_safety_gate`
- `packet_id=packet_o3_28_pose_same_task_replay_7d57826142b0c79c`
- `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`
- `route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`
- `route_csv_row_count=28`
- `segment_count=27`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `safe_to_control=false`
- `robot_control_executed=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`

`bounded_command_caps`、`segment_distance_summary`、`bounded_segment_plan` 和 `global_abort_criteria` 只用于未来受控执行计划输入，不是实际控制命令。下一步 live execution 仍阻塞在 operator approval、current live HIL / stop path、同窗口 LiDAR/localization/TF readiness、Nav2/controller execution result 和 delivery/operator acceptance evidence。

## 验证结果

`python3 -m py_compile onboard/scripts/o3_bounded_route_command_plan.py`

```text
exit 0, no stdout
```

`python3 -m unittest onboard.tests.test_o3_bounded_route_command_plan`

```text
....
----------------------------------------------------------------------
Ran 4 tests in 0.006s

OK
```

`python3 onboard/scripts/o3_bounded_route_command_plan.py --gate-record sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record/artifacts/algorithm/controlled_route_execution_gate_record.json --output-dir sprints/2026.07.13_08-09_o3_bounded_route_command_plan/artifacts/algorithm`

```text
{"status": "ok", "artifact": "sprints/2026.07.13_08-09_o3_bounded_route_command_plan/artifacts/algorithm/bounded_route_command_plan.json", "execution_plan_status": "blocked_pending_live_safety_gate", "segment_count": 27}
```

`python3 -m json.tool sprints/2026.07.13_08-09_o3_bounded_route_command_plan/artifacts/algorithm/bounded_route_command_plan.json >/tmp/o3_bounded_route_command_plan.pretty.json`

```text
exit 0, no stdout
```

Structured acceptance assert:

```text
bounded_route_command_plan_acceptance_ok
```

Artifact distance/caps readback:

```text
execution_plan_status=blocked_pending_live_safety_gate
route_csv_row_count=28
segment_count=27
total_distance_m=0.723849
max_segment_distance_m=0.05
min_segment_distance_m=0.023849
average_segment_distance_m=0.026809
nonzero_segment_count=27
estimated_duration_s_at_cap=7.238
max_linear_speed_mps=0.1
max_angular_speed_radps=0.3
route_timeout_s=120.0
route_deviation_abort_threshold_m=0.15
```

`rg -n "bounded_route_command_plan|packet_o3_28_pose_same_task_replay_7d57826142b0c79c|blocked_pending_live_safety_gate|route_execution_success=false|safe_to_control=false|no /cmd_vel|no /api/base/manual|no NavigateToPose|no WAVE ROVER UART" ...`

```text
onboard/scripts/o3_bounded_route_command_plan.py:23:PLAN_SCHEMA = "trashbot.o3.bounded_route_command_plan.v1"
onboard/scripts/o3_bounded_route_command_plan.py:27:EXPECTED_PACKET_ID = "packet_o3_28_pose_same_task_replay_7d57826142b0c79c"
onboard/scripts/o3_bounded_route_command_plan.py:364:        "execution_plan_status": "blocked_pending_live_safety_gate",
onboard/scripts/o3_bounded_route_command_plan.py:398:            "route_execution_success=false",
onboard/scripts/o3_bounded_route_command_plan.py:399:            "safe_to_control=false",
onboard/tests/test_o3_bounded_route_command_plan.py:117:            self.assertEqual("blocked_pending_live_safety_gate", plan["execution_plan_status"])
docs/navigation/fixed_route_workflow.md:3182:`bounded_route_command_plan` 合同。Algorithm helper 只读取
sprints/2026.07.13_08-09_o3_bounded_route_command_plan/artifacts/algorithm/bounded_route_command_plan.json:610:  "execution_plan_status": "blocked_pending_live_safety_gate",
sprints/2026.07.13_08-09_o3_bounded_route_command_plan/artifacts/algorithm/bounded_route_command_plan.json:695:  "packet_id": "packet_o3_28_pose_same_task_replay_7d57826142b0c79c",
exit 0
```

`git diff --check -- onboard/scripts/o3_bounded_route_command_plan.py onboard/tests/test_o3_bounded_route_command_plan.py docs/navigation/fixed_route_workflow.md sprints/2026.07.13_08-09_o3_bounded_route_command_plan`

```text
exit 0, no stdout
```

## 失败定位和修复记录

验证未出现失败。实现中主动加入 fail-closed 失败路径：07:07 gate record 的 schema、identity、count/status、literal guard、fixed false field 或 route CSV 行数/字段/order/strict_no_motion 任一漂移时抛出 `PlanInputError`；CLI 返回非零 `blocked_bounded_route_command_plan_input_mismatch`，不会写出 bounded plan artifact。

## 剩余风险和下一步能力建设建议

本轮仍只是 `software_proof_o3_o1_no_motion_bounded_route_command_plan_only`。它证明同一 07:07 gate record 和 28 行 route CSV 可生成 bounded route execution command plan with abort criteria，不证明真实 route execution、Nav2/controller/BT 执行、`/cmd_vel`、`/api/base/manual`、WAVE ROVER UART、delivery/operator acceptance、current live HIL 或 safe-to-control。OKR 主百分比不应因本轮 no-motion plan 单独上调，KR `不归档`。

下一步能力建设建议：另开受控 live execution sprint，先补 explicit operator approval、current live HIL/stop path、同窗口 `/scan`、`/amcl_pose`、`/tf`、`/map` readiness，再用同一 `packet_id` / `route_intent_id` 收集 Nav2/controller execution result；只有这些现场证据齐备后，才能讨论任何控制或成功字段变化。
