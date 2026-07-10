# O6 Worker Report

## 改动文件

- `/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `/Users/m1/apps/rober/docs/interfaces/o6_cloud_archive_api.md`

## 实现内容

- 在 O6 field evidence manifest ingest 与 artifact bundle ingest 中新增 `field_motion_evidence_packet` additive 摘要接入。
- `field_motion_evidence_packet` 固定只回读保守字段：
  - `schema=trashbot.field_motion_evidence_packet.v1`
  - `proof_scope=software_proof_field_motion_evidence_packet_only`
  - `status`
  - `route_summary.frame_count/nonzero_displacement_observed/displacement_m`
  - `motion_log_summary.live_motion_evidence_present/evidence_sources`
  - `route_bag_or_live_nav2_log.present/source/route_bag_present/live_motion_log_present`
  - `blocked_reasons`
  - `next_required_evidence`
  - 四个 false safety flags
- 对 `path/root/token/raw/base64` 等危险内容不回显；缺包时返回 `blocked_not_proven` 占位摘要。
- 将同一摘要同步暴露到：
  - archive task detail `task.field_motion_evidence_packet`
  - `task.field_evidence.field_motion_evidence_packet`
  - `task.field_evidence_consumer_ingest.field_motion_evidence_packet`
  - `task.artifact_bundle.field_motion_evidence_packet`
  - consumer detail 顶层 alias `field_motion_evidence_packet`
- 单测覆盖：
  - field evidence manifest ingest/readback
  - artifact bundle ingest/readback
  - packet 缺失时 blocked summary
  - unsafe path 不回显、四个 safety flags 保持 false

## 验证结果

```text
$ PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
OK

$ PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
Ran 155 tests in 53.281s
OK
```

## 给 O7 / Product 的 O6 回读字段摘要

- `field_motion_evidence_packet.status`
  - `field_motion_packet_ready_not_delivery_proof`
  - 或缺包时 `blocked_not_proven`
- `field_motion_evidence_packet.route_summary`
  - `frame_count`
  - `nonzero_displacement_observed`
  - `displacement_m`
- `field_motion_evidence_packet.motion_log_summary`
  - `live_motion_evidence_present`
  - `evidence_sources`
- `field_motion_evidence_packet.route_bag_or_live_nav2_log`
  - `present`
  - `source`
  - `route_bag_present`
  - `live_motion_log_present`
- `field_motion_evidence_packet.blocked_reasons`
- `field_motion_evidence_packet.next_required_evidence`
- `field_motion_evidence_packet.safe_to_control=false`
- `field_motion_evidence_packet.delivery_success=false`
- `field_motion_evidence_packet.primary_actions_enabled=false`
- `field_motion_evidence_packet.robot_control_executed=false`

## 剩余风险

- 仍然只是 local/mock archive readback，不证明真实生产云、真实 route bag、真实 Nav2 live run、真实 delivery success。
- 当前 `motion_log_summary.evidence_sources` 只保留短标签；如果算法侧后续要新增枚举值，需要继续保持不回显路径/root/token/raw/base64。
