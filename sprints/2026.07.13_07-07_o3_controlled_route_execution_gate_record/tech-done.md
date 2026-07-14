# Tech Done - O3 Controlled Route Execution Gate Record

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record/`
- Owner: `robot-algorithm-engineer`
- Proof boundary: `software_proof_o3_o1_fail_closed_controlled_route_execution_gate_record_only`
- Artifact: `sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record/artifacts/algorithm/controlled_route_execution_gate_record.json`

## 自主能力目标和本轮抓手

本轮目标不是执行路线，而是把 05:02 accepted same-task replay packet 转成受控 route execution 前的 fail-closed gate record。抓手是复核 exact `packet_id=packet_o3_28_pose_same_task_replay_7d57826142b0c79c`、`task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`、`route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`、28/28/28 counts 和 source hashes；通过后仍保持 `route_execution_success=false`、`safe_to_control=false`。

本轮保持 no-motion/control guard：no /cmd_vel、no /api/base/manual、no NavigateToPose、no WAVE ROVER UART。未调用 ROS2 action、controller/BT、manual base、UART 或任何机器人运动命令。

## 实际改动文件和接口影响

- `onboard/scripts/o3_controlled_route_execution_gate_record.py`
- `onboard/tests/test_o3_controlled_route_execution_gate_record.py`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record/artifacts/algorithm/controlled_route_execution_gate_record.json`
- `sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record/tech-done.md`

接口影响：只新增本地 Algorithm artifact contract `trashbot.o3.controlled_route_execution_gate_record.v1`，不新增 ROS2 topic/action/service，不改变 O6/O7 consumer API，不改变 hardware driver、launch、production cloud 或 `OKR.md`。

## 实现内容

新增 `o3_controlled_route_execution_gate_record.py`，只读取 05:02 `same_task_replay_packet_summary.json` 和其 refs 指向的 04:02 summary、route CSV、replay JSONL、05:02 packet JSONL。生成器会在写出前执行：

- identity 校验：packet/task/route intent 必须与 05:02 Product accepted identity 完全一致；
- count 校验：route CSV、replay JSONL、packet JSONL 和 path structured pose count 必须均为 28；
- hash 校验：`summary_sha256=9948414e1a46b6e78de5503a06d634e24c5e96aff38c1f4c7d756bd20eb0dc93`、`route_csv_sha256=61b4020c93f01e595df4608e8b42545ce1b1d04eaff8798db55b0dda2aae7601`、`replay_jsonl_sha256=530941a7ecb4768f6583cda4abca0d9bc92715ea0266fc96e83d3a860a0400b5` 必须同时匹配 packet summary 声明值和当前文件重算值；
- fail-closed guard：任何 source mismatch 都返回非零 `blocked_source_packet_mismatch`，不会写出 route-execution-ready 状态。

新增单测覆盖有效输入、packet identity 漂移、source hash 漂移和 `safe_to_control=true` 漂移。导航文档追加 07:07 gate record 合同，明确该 artifact 不能被升级为 route execution、delivery、HIL 或 safe-to-control。

## Gate Record 结果

生成的 artifact 关键字段：

- `schema=trashbot.o3.controlled_route_execution_gate_record.v1`
- `controlled_route_execution_gate_status=fail_closed_input_packet_validated`
- `identity_validation_status=pass_exact_same_task_identity`
- `count_validation_status=pass_exact_28_28_28`
- `source_hash_validation_status=pass_exact_source_hashes`
- `route_csv_row_count=28`
- `replay_jsonl_event_count=28`
- `packet_jsonl_event_count=28`
- `path_structured_pose_count=28`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `safe_to_control=false`
- `robot_control_executed=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`

`next_live_command_gate` 继续要求：人工安全复核或等价安全 gate、current live HIL / stop path / controlled environment material、bounded route execution command plan with abort criteria、同窗口 LiDAR/localization/TF readiness、Nav2/controller execution result 和 delivery/operator acceptance evidence。

## 验证结果

`python3 -m py_compile onboard/scripts/o3_controlled_route_execution_gate_record.py`

```text
exit 0, no stdout
```

`python3 -m unittest onboard.tests.test_o3_controlled_route_execution_gate_record`

```text
....
----------------------------------------------------------------------
Ran 4 tests in 0.008s

OK
```

`python3 onboard/scripts/o3_controlled_route_execution_gate_record.py --packet-summary sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/artifacts/algorithm/same_task_replay_packet_summary.json --output-dir sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record/artifacts/algorithm`

```text
{"status": "ok", "artifact": "sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record/artifacts/algorithm/controlled_route_execution_gate_record.json", "controlled_route_execution_gate_status": "fail_closed_input_packet_validated"}
```

`python3 -m json.tool sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record/artifacts/algorithm/controlled_route_execution_gate_record.json >/tmp/o3_controlled_route_execution_gate_record.pretty.json`

```text
exit 0, no stdout
```

Structured assertion from tech-plan adapted to artifact:

```text
controlled_route_execution_gate_record_acceptance_ok
```

`rg -n "controlled_route_execution_gate_record|packet_o3_28_pose_same_task_replay_7d57826142b0c79c|route_execution_success=false|safe_to_control=false|no /cmd_vel|no /api/base/manual|no NavigateToPose|no WAVE ROVER UART|robot-algorithm-engineer" onboard/scripts/o3_controlled_route_execution_gate_record.py onboard/tests/test_o3_controlled_route_execution_gate_record.py docs/navigation/fixed_route_workflow.md sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record/tech-done.md sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record/artifacts/algorithm/controlled_route_execution_gate_record.json`

```text
sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record/artifacts/algorithm/controlled_route_execution_gate_record.json:82:  "packet_id": "packet_o3_28_pose_same_task_replay_7d57826142b0c79c",
sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record/artifacts/algorithm/controlled_route_execution_gate_record.json:109:    "route_execution_success=false",
sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record/artifacts/algorithm/controlled_route_execution_gate_record.json:110:    "safe_to_control=false",
sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record/artifacts/algorithm/controlled_route_execution_gate_record.json:111:    "no /cmd_vel",
sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record/artifacts/algorithm/controlled_route_execution_gate_record.json:112:    "no /api/base/manual",
sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record/artifacts/algorithm/controlled_route_execution_gate_record.json:113:    "no NavigateToPose",
sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record/artifacts/algorithm/controlled_route_execution_gate_record.json:114:    "no WAVE ROVER UART",
onboard/scripts/o3_controlled_route_execution_gate_record.py:16:# 本脚本是 robot-algorithm-engineer 的 no-motion gate，不 import ROS2，也不提供任何控制参数。
docs/navigation/fixed_route_workflow.md:3167:`controlled_route_execution_gate_record` 合同。Algorithm helper 只读取
exit 0
```

`git diff --check -- onboard/scripts/o3_controlled_route_execution_gate_record.py onboard/tests/test_o3_controlled_route_execution_gate_record.py docs/navigation/fixed_route_workflow.md sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record`

```text
exit 0, no stdout
```

## 失败定位和修复记录

未出现验证失败。实现中主动加入 fail-closed 失败路径：identity、count、source hash 或 safety false field 任一漂移时抛出 `GateInputError`；CLI 返回非零并输出 `blocked_source_packet_mismatch`，不会生成 execution-ready artifact。

## 剩余风险

本轮仍只是 `software_proof_o3_o1_fail_closed_controlled_route_execution_gate_record_only`。它证明同一 05:02 packet 可被受控执行前 gate 消费和复核，不证明真实 route execution、Nav2/controller/BT 执行、`/cmd_vel`、`/api/base/manual`、WAVE ROVER UART、delivery/operator acceptance、current live HIL 或 safe-to-control。OKR 主百分比不应因本轮 fail-closed gate 单独上调，KR `不归档`。

下一步能力建设建议：另开受控 live execution sprint，并在安全 operator approval、current live HIL/stop path、bounded command plan、同窗口 LiDAR/localization/TF readiness 和 Nav2/controller execution result 可记录后，才允许讨论任何控制或成功字段变化。
