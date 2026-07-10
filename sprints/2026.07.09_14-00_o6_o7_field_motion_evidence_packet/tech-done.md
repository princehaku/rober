# O6/O7 Field Motion Evidence Packet Tech Done

## sprint_type: epic

## 实际改动

- Algorithm 交付了 `field_motion_evidence_packet` 收口：`field_route_evidence_manifest.py` 新增 `--motion-log-root`，并在同一 manifest 中输出 `field_motion_evidence_manifest.json` 与 `derived_replay.jsonl`。
- O6 将 `field_motion_evidence_packet` additive 接入 `remote_cloud_relay.py` 的 field evidence manifest / artifact bundle ingest 与 readback 主路径，支持顶层和 nested alias 回读。
- O7 将 `field_motion_evidence_packet` 接入 consumer detail、artifact bundle readiness、route replay、labeling workspace 的消费主路径，并对 `dangerous true`、schema mismatch、unsafe text 继续 fail-closed。
- Product 完成本 sprint 收口文档，并同步更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。

## 核心证据

- packet schema：`trashbot.field_motion_evidence_packet.v1`
- proof scope：`software_proof_field_motion_evidence_packet_only`
- route replay：`derived_replay.jsonl` 共 `17` 帧
- route 位移：`distance_m=0.167998`
- 运动证据：`nonzero_displacement_observed=true`
- live motion：`live_motion_evidence_present=true`
- route_bag_or_live_nav2_log：`present=true`、`source=live_motion_log`、`route_bag_present=false`
- safety flags：`safe_to_control: false`、`delivery_success: false`、`primary_actions_enabled: false`、`robot_control_executed: false`

## 验证结果

- Algorithm：
  - `python3 -m unittest onboard/tests/test_field_route_evidence_manifest.py`
  - 结果：`Ran 13 tests in ... OK`
  - `python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py` 通过
  - 生成命令结果：`gate_pass=true`，`status=field_evidence_manifest_ready_not_delivery_proof`
- O6：
  - `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py` 通过
  - `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`
  - 结果：`Ran 155 tests in 53.281s OK`
  - `git diff --check` 通过
- O7：
  - `cd pc-tools/workstation && npm run test`
  - 结果：`3 passed` / `476 passed`
  - `cd pc-tools/workstation && npm run build` 通过
  - `cd pc-tools/workstation && npm run lint` 通过
  - `git diff --check` 通过

## OKR 影响

- O6：约 `47% -> 50%`。理由是同一 `task_id` 的 field motion evidence packet 已从 Algorithm 产物贯通到 O6 archive ingest/readback，且具备 `155 tests` 的 readback 证据。
- O7：约 `47% -> 50%`。理由是 O7 已能消费同一 packet 到 consumer detail、artifact bundle readiness、route replay、labeling workspace，且通过 `476 passed`、build、lint。
- 本轮不归档任何 KR。原因是证据边界仍是 `software_proof_field_motion_evidence_packet_only`，不证明真实 production cloud、真实 `route_bag`、真实 Nav2 live run、真实 delivery success、真实 OSS/CDN、真实 annotation API/export。

## 偏差与未完成事项

- packet 已有 live motion log 证据，但 `route_bag` 仍缺失，只能作为 `route_bag_or_live_nav2_log` 的 live motion 分支成立。
- `direct_odom_capture_nonzero=false`，说明现场运动链路仍缺更强的非零 odom / bag replay 证据。
- `source_manifest_task_id_missing` 仍存在，因此当前 `task_id` 由 fallback 生成，不是源现场材料原生携带。

## 剩余风险

- 不证明真实生产云、生产 DB/queue、TLS/4G、OSS/CDN、真实 annotation API/export、真实媒体访问。
- 不证明真实 `route_bag`、真实 Nav2 live run、真实机器人控制、wheel raw 非零或 delivery success。
- 不证明完整路线长期验收、真实电梯状态链、真实 RTC/视频、真实 ASR/TTS。
