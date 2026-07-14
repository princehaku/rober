# Tech Done - O3 28-Pose Same-Task Replay Packet

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/`
- Owner: `robot-algorithm-engineer`
- Status: implementation and verification passed
- Closeout time: 2026-07-13 05:15 CST
- Proof boundary: `software_proof_o3_o1_strict_no_motion_same_task_route_replay_packet_only`

## 自主能力目标和本轮抓手

本轮目标是消费 04:02 accepted material 的 summary、`route_csv` 和 `replay_jsonl`，生成同一 `task_id` / `route_intent_id` 的 strict no-motion same-task route replay packet。

本轮抓手不是重新导出路线，也不是复制 summary 文案，而是让 Algorithm offline consumer 实际读取 28 行 CSV 和 28 行 JSONL，交叉校验 identity、order/source_index、frame、stamp、position、orientation 和 source fingerprint。

## 改动文件和接口影响

- `onboard/scripts/o3_28_pose_same_task_replay_packet.py`
- `onboard/tests/test_o3_28_pose_same_task_replay_packet.py`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/artifacts/algorithm/same_task_replay_packet_summary.json`
- `sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/artifacts/algorithm/same_task_route_replay_packet.jsonl`
- `sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/tech-done.md`

接口影响：新增离线脚本和离线 packet artifact，不改 ROS2 runtime、launch、Nav2 action、controller/BT、`/cmd_vel`、`/api/base/manual`、WAVE ROVER UART、硬件配置或 O5/O6/O7/UI 代码。

## 实现内容

`o3_28_pose_same_task_replay_packet.py` 新增 fail-closed 三方读取：

- 读取 04:02 summary，校验 `schema=trashbot.fixed_route_28_pose_consumer.v1`、`task_id`、`route_intent_id`、`fresh_28_pose_structured_material_consumed=true`、`historic_21_57_artifact_primary_source=false`、`path_structured_pose_count=28` 和 safety false fields。
- 读取 04:02 `fixed_route_28_pose_route.csv`，校验 header、28 rows、`schema=trashbot.fixed_route_28_pose_route_csv.v1`、同一 identity、`strict_no_motion=true`、order/source_index 连续和 pose 字段完整。
- 读取 04:02 `fixed_route_28_pose_replay.jsonl`，校验 28 events、`schema=trashbot.fixed_route_28_pose_replay.v1`、`event=structured_pose`、同一 identity、`strict_no_motion=true`、`route_execution_success=false` 和 pose 字段完整。
- 逐 pose 对比 CSV 与 JSONL 的 order/source_index、frame、stamp、position、orientation 和 primary source artifact，任一漂移都直接失败。
- 输出 deterministic `packet_id`、三份 source sha256、first/last pose readback、28 行 packet JSONL，以及全部 safety false fields。

输出 summary 关键字段：

- `schema=trashbot.o3.same_task_route_replay_packet.v1`
- `packet_id=packet_o3_28_pose_same_task_replay_7d57826142b0c79c`
- `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`
- `route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`
- `route_csv_row_count=28`
- `replay_jsonl_event_count=28`
- `path_structured_pose_count=28`
- `same_task_identity_verified=true`
- `same_task_replay_packet_ready=true`
- `consumer_integration_status=pass_strict_no_motion_same_task_replay_packet`

## 测试、dry-run 或上车验证结果

已运行验收命令并通过：

```text
python3 -m py_compile onboard/scripts/o3_28_pose_same_task_replay_packet.py
# exit 0

python3 -m unittest onboard.tests.test_o3_28_pose_same_task_replay_packet
....
----------------------------------------------------------------------
Ran 4 tests in 0.012s

OK

python3 onboard/scripts/o3_28_pose_same_task_replay_packet.py --summary ... --route-csv ... --replay-jsonl ... --output-dir ...
{"status": "ok", "summary": "sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/artifacts/algorithm/same_task_replay_packet_summary.json"}

python3 -m json.tool .../same_task_replay_packet_summary.json >/tmp/o3_28_pose_same_task_replay_packet_summary.pretty.json
# exit 0

structured assertions
o3_28_pose_same_task_replay_packet_ok

rg -n "same-task|28-pose|route_csv|replay_jsonl|route_execution_success=false|delivery_success=false|hil_pass=false|safe_to_control=false|robot-algorithm-engineer" ...
# exit 0, anchors found in sprint docs/artifacts and docs/navigation/fixed_route_workflow.md

git diff --check -- onboard/scripts/o3_28_pose_same_task_replay_packet.py onboard/tests/test_o3_28_pose_same_task_replay_packet.py docs/navigation/fixed_route_workflow.md sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet
# exit 0
```

## 数据、样本或调试输出变化

- Source summary SHA256: `9948414e1a46b6e78de5503a06d634e24c5e96aff38c1f4c7d756bd20eb0dc93`
- Source route CSV SHA256: `61b4020c93f01e595df4608e8b42545ce1b1d04eaff8798db55b0dda2aae7601`
- Source replay JSONL SHA256: `530941a7ecb4768f6583cda4abca0d9bc92715ea0266fc96e83d3a860a0400b5`
- Packet JSONL line count: 28
- First pose: `source_index=0`, `frame_id=map`, `x=0.07615115310756959`, `y=0.2500000037252903`
- Last pose: `source_index=27`, `frame_id=map`, `x=0.8`, `y=0.2500000037252903`

## 失败定位

本轮实现和验收没有出现失败。脚本已把潜在失败收敛到输入合同：summary identity 漂移、source refs 不匹配、CSV/JSONL 非 28 行、pose order/source_index 不连续、CSV 与 JSONL pose 字段不一致、source fingerprint 输入被替换，或任何 safety 字段变 true 时，都会 fail closed，不生成可接受 packet。

## 运动/控制路径声明

未触发任何运动或控制路径。未运行 NavigateToPose、controller/BT、`/cmd_vel` 发布、`/api/base/manual` 调用、WAVE ROVER UART、route execution、delivery、HIL 或 safe-to-control path。

输出 artifact 固定：

- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `safe_to_control=false`
- `robot_control_executed=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`

## 剩余风险和下一步能力建设建议

剩余风险：

- 本轮仍是 strict no-motion offline packet，不是 fixed-route movement、Nav2 route execution、delivery/operator acceptance、current live HIL、safe-to-control 或 O5 production external evidence。
- 04:02 source 仍来自 03:00 28-pose material；没有复现旧 21-pose expectation，若仍要求 21 点，需要另开 current live localization/map-bound drift 复验。
- O6/O7 archive/readback 未纳入本轮范围；如果要让云端或 PC 消费 packet，应另开跨 owner sprint。

下一步建议：在安全准入明确后，用同一 `packet_id` / `route_intent_id` 规划受控 route execution evidence；在此之前不要再重复 helper/export/readiness/route-intent 包装。
