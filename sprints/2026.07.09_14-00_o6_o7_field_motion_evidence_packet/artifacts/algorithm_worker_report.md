# Algorithm Worker Report

## 自主能力目标和本轮抓手

- 目标：把 2026-06-10 现场 `map/route/keyframes/remote_capture` 归一成同一 `task_id` 的 `field_motion_evidence_packet`，供 O6 ingest 与 O7 replay/readiness 消费。
- 抓手：复用 `route.csv`、`manifest.json`、keyframes、`learn_launch.log`、`pulse_and_stop2.log`、`odom_after_motion*.txt`、`tf_after_motion*.txt`，并派生同轮 `derived_replay.jsonl`。

## 改动文件和接口影响

- `onboard/scripts/field_route_evidence_manifest.py`
  - 新增 `field_motion_evidence_packet` 摘要。
  - 新增 `--motion-log-root` 参数。
  - 新增 route / keyframe / map / motion log 摘要与 lineage fallback 逻辑。
- `onboard/tests/test_field_route_evidence_manifest.py`
  - 新增 route-root + live motion log packet 单测。
  - 同步修正 route-root seed 下 `route_bag` optional 语义断言。
- `docs/navigation/field_route_evidence_manifest.md`
  - 补充 `field_motion_evidence_packet`、`--motion-log-root` 与 live motion fallback 说明。

## 实现内容

- `field_motion_evidence_packet.schema=trashbot.field_motion_evidence_packet.v1`
- `proof_scope=software_proof_field_motion_evidence_packet_only`
- `task_id=field_motion_evidence_packet_20260709`
- `task_id_source=run_id_fallback_due_missing_source_task_id`
- `route_id=dynamic_odom_tf_20260610`
- `route_summary.frame_count=17`
- `route_summary.nonzero_displacement_observed=true`
- `route_summary.distance_m=0.167998`
- `motion_log_summary.live_motion_evidence_present=true`
- `motion_log_summary.evidence_sources`
  - `learn_launch.log:nonzero_waypoints`
  - `pulse_and_stop2.log:nonzero_cmd_vel`
  - `tf_after_motion2.txt:nonzero_translation`
  - `route.csv:nonzero_displacement`
- `route_bag_or_live_nav2_log.present=true`
- `route_bag_or_live_nav2_log.source=live_motion_log`
- 所有危险字段继续保持：
  - `safe_to_control=false`
  - `delivery_success=false`
  - `primary_actions_enabled=false`
  - `robot_control_executed=false`

## 测试、dry-run 或上车验证结果

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/tests/test_field_route_evidence_manifest.py`
  - `Ran 13 tests in 0.044s`
  - `OK`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py`
  - 通过
- `python3 onboard/scripts/field_route_evidence_manifest.py ... --run-id field_motion_evidence_packet_20260709`
  - `gate_pass=true`
  - `status=field_evidence_manifest_ready_not_delivery_proof`

## 数据、样本或调试输出变化

- 新增 [`/Users/m1/apps/rober/sprints/2026.07.09_14-00_o6_o7_field_motion_evidence_packet/artifacts/derived_replay.jsonl`](/Users/m1/apps/rober/sprints/2026.07.09_14-00_o6_o7_field_motion_evidence_packet/artifacts/derived_replay.jsonl)
  - `17` 行 replay frame
- 新增 [`/Users/m1/apps/rober/sprints/2026.07.09_14-00_o6_o7_field_motion_evidence_packet/artifacts/field_motion_evidence_manifest.json`](/Users/m1/apps/rober/sprints/2026.07.09_14-00_o6_o7_field_motion_evidence_packet/artifacts/field_motion_evidence_manifest.json)
  - 含 `field_motion_evidence_packet`
- 新增本报告 [`/Users/m1/apps/rober/sprints/2026.07.09_14-00_o6_o7_field_motion_evidence_packet/artifacts/algorithm_worker_report.md`](/Users/m1/apps/rober/sprints/2026.07.09_14-00_o6_o7_field_motion_evidence_packet/artifacts/algorithm_worker_report.md)

## 给 O6/O7 worker 的合同字段摘要

- `field_motion_evidence_packet.schema`
- `field_motion_evidence_packet.proof_scope`
- `field_motion_evidence_packet.task_id`
- `field_motion_evidence_packet.task_id_source`
- `field_motion_evidence_packet.route_id`
- `field_motion_evidence_packet.map_summary`
- `field_motion_evidence_packet.route_summary`
- `field_motion_evidence_packet.keyframe_summary`
- `field_motion_evidence_packet.motion_log_summary`
- `field_motion_evidence_packet.derived_replay_summary`
- `field_motion_evidence_packet.route_bag_or_live_nav2_log`
- `field_motion_evidence_packet.blocked_reasons`
- `field_motion_evidence_packet.next_required_evidence`
- `field_motion_evidence_packet.safe_to_control=false`
- `field_motion_evidence_packet.delivery_success=false`
- `field_motion_evidence_packet.primary_actions_enabled=false`
- `field_motion_evidence_packet.robot_control_executed=false`

## 剩余风险和下一步能力建设建议

- 现场 source `manifest.json` 的 `task_id` 为空，本轮只能回退到 `run_id` 作为 packet `task_id`。
- `odom_after_motion*.txt` 仍未证明非零，当前只由 `route.csv`、waypoint 记录、`pulse_and_stop2.log` 和 `tf_after_motion2.txt` 支撑 motion evidence。
- `route_bag` 仍缺失，因此 `route_bag_or_live_nav2_log` 目前是 live motion log fallback，不是 rosbag / Nav2 completion proof。
- 下一步优先补同一 `task_id` 的 `route_bag` 或带 pose progression 的 live Nav2 log，再把该 packet 交给 O6 ingest / O7 consumer 读取。
