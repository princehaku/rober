# O7 真实相机关键帧标注流 Epic - PRD

## 状态与产品问题
- `sprint_type: epic`
- 阶段：`prd_complete`；本轮只规划，不运行 SSH/live/test。
- O6/O7 已有 local/mock labeling/consumer 合同，但没有本轮真实相机帧；上一轮 scan inventory 又未产出 DB3/keyframe/replay。
- O5 provider blocker 已消费两轮，禁止第三轮；本轮选择不依赖 scan/provider 的真实 camera 单帧链。

## 用户价值、北极星和成功定义
- 用户：数据标注运营、Algorithm Engineer、Product 验收人。
- 价值：明确帧的真实来源、topic/stamp、尺寸/编码、媒体 hash、隐私边界与 annotation-ready 身份。
- 北极星 `current_live_camera_keyframe_consumed_for_annotation=true` 仅在 inventory daemon-off、唯一单帧、PNG/hash/manifest、O6/O7 same-task lineage、只读 UI 和固定 false safety fields 全 clean 时成立。
- fixture-only 只能为 `software_contract_ready_live_keyframe_not_captured`。

## 冻结 schema
- Algorithm：`trashbot.o7.live_camera_keyframe_manifest.v1`。
- O6 section：`trashbot.o6.live_camera_keyframe_annotation_material.v1`，放入既有 artifact-bundle/task-detail；禁止新 endpoint/wrapper。
- O7 consumer：`trashbot.pc_tools_workstation.o7_live_camera_keyframe_annotation_ready.v1`。
- 必需字段：`schema, task_id, source_mode, source_proof, topic, message_type, publisher_count_at_inventory, stamp_sec, stamp_nanosec, width, height, step, encoding, is_bigendian, media_basename, media_byte_size, sha256, captured_at_utc, inventory_ssh_invocation_count, single_frame_capture_invocation_count, redaction_boundary, annotation_ready`。
- 四 delta 与 `safe_to_control, robot_control_executed, route_execution_success, delivery_success, hil_pass` 必须显式存在。
- `redaction_boundary` 必含 `classification, raw_pixels_in_manifest=false, binary_inline_in_api=false, binary_logged=false, absolute_path_exposed=false, remote_host_exposed=false, ui_metadata_only=true, privacy_review_status, media_access_scope=sprint_local_artifact_only`。

## P0 产品流程
1. Algorithm 与 Full-stack 按不重叠文件并行，后者先用 synthetic fixture。
2. Algorithm 最多一次 `ROS2CLI_NO_DAEMON=1` SSH inventory；选择既有唯一 `sensor_msgs/msg/Image` publisher。
3. gate blocked 则 capture count 0；gate clean 才最多一次 subscription，收到第一帧立即退出，失败不 retry。
4. Algorithm 校验 stamp/dimensions/step/data length/encoding，生成 canonical PNG、SHA-256、manifest 和 receipt。
5. Full-stack 用同一 manifest 走 O6 artifact-bundle/task-detail 和 O7 consumer-detail；不得内联 PNG。
6. Product 按 live/fixture/blocked 事实决定四 delta、OKR/KR 与收口。

## Clean / Blocked 验收
- Clean live：inventory/capture 精确 `1/1`；无 daemon/runtime/topic/control mutation；PNG 非空且 hash/size 一致；O6/O7 的 task/hash/topic/stamp/dimensions/encoding 一致；UI 明示 source/redaction/annotation status。
- Blocked：无 publisher、wrong type、0/multiple candidates、daemon drift、依赖缺失时 capture 0；唯一 capture timeout/invalid layout/unsupported encoding/hash 失败时 capture 1 但 current delta false。
- Fixture：可通过 schema/UI 测试，但 `source_proof=fixture_contract_only`、四 delta=false、无 live badge。
- 任一危险 true、unsafe ref、binary inline、source/invocation mismatch 必须 fail closed。

## Mission Objective 0 与 OKR
- 仅 clean live chain 可使 `current_run_artifact_delta=true`；fixture/inventory/partial 均 false。
- `external_artifact_delta=false`、`live_control_delta=false`、`user_action_delta=false`；Mission Objective 0 本轮仍未满足。
- 规划期 O5 85%、O6/O7 93%、O1 94% 均不变，KR 不归档；final 只可凭真实 live lineage 保守判断小幅进展。

## 禁止项、风险和历史
- 禁止 scan/rosbag、O5 provider、preflight/readback/export/status/browser/voice/packet/mock wrapper；禁止启动 camera/bringup/launch/service。
- 禁止 `/initialpose`、`/cmd_vel`、`/api/base/manual`、NavigateToPose、topic pub、action/service write、UART/运动。
- annotation-ready 只表示稳定条目身份，不表示隐私批准、已提交标注、真实 RTC/video、production cloud/DB/OSS、route/delivery/HIL。
- 本阶段无已完成 KR，不移动历史区；后续证据必须链接本 sprint docs/artifacts 并保留上述风险。
