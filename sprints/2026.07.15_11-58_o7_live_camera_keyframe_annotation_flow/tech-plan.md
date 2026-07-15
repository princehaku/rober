# O7 真实相机关键帧标注流 Epic - Tech Plan

## 状态与 OKR 最低优先级核对
- `sprint_type: epic`；状态：`tech_plan_complete_ready_for_two_owner_parallel_dispatch`；本轮只规划，不运行 SSH/live/test。
- 最低 Objective 是 O5 约 85%；本 sprint 不做 O5，因为 `provider_runtime_preflight` 已两轮封顶，第三轮禁止。
- O6/O7 各约 93%；本轮改做真实 camera keyframe。最新 scan dataset inventory 已 blocked/退役，不得重跑。
- final 必须复核 O5 blocker 是否仍成立、是否真实产生 live keyframe；fixture-only 不得加分。

## 冻结 schema 和状态
- Input `trashbot.o7.live_camera_keyframe_manifest.v1` 必含：`task_id, source_mode, source_proof, topic, message_type=sensor_msgs/msg/Image, publisher_count_at_inventory, stamp_sec, stamp_nanosec, width, height, step, encoding, is_bigendian, media_basename, media_byte_size, sha256, captured_at_utc, inventory_ssh_invocation_count, single_frame_capture_invocation_count, redaction_boundary, annotation_ready, blocked_reasons, not_proven`。
- `redaction_boundary` 必含：`classification, raw_pixels_in_manifest=false, binary_inline_in_api=false, binary_logged=false, absolute_path_exposed=false, remote_host_exposed=false, ui_metadata_only=true, privacy_review_status, media_access_scope=sprint_local_artifact_only`。
- O6 `trashbot.o6.live_camera_keyframe_annotation_material.v1` 放入既有 artifact-bundle/task-detail；O7 `trashbot.pc_tools_workstation.o7_live_camera_keyframe_annotation_ready.v1` 放入既有 consumer-detail/UI；禁止新 endpoint/wrapper。
- Live clean：`source_proof=live_single_frame_captured`、invocation `1/1`、`annotation_ready=true`、仅 current delta true；fixture：`source_proof=fixture_contract_only`、状态 `annotation_ready_fixture_contract_only`、四 delta false；blocked 不得 annotation-ready。
- 三层保留同一 `task_id + sha256 + topic + stamp + width + height + encoding`；unsafe ref/raw/base64/dangerous true/source-count mismatch 必须 fail closed。

## 两个 owner 精确且不重叠文件范围
- `robot-algorithm-engineer`：`onboard/scripts/o7_live_camera_keyframe_capture.py`；`onboard/tests/test_o7_live_camera_keyframe_capture.py`；`docs/vision/o7_live_camera_keyframe_capture.md`；本 sprint `artifacts/algorithm/{read_only_camera_inventory.json,live_camera_keyframe_manifest.json,live_camera_keyframe_capture_receipt.json,keyframe.png}`；本 sprint `tech-done.md`。
- `full-stack-software-engineer`：`onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`；其 `test/test_remote_cloud_relay.py`；`pc-tools/workstation/src/{server/o7ConsumerReadAdapter.ts,shared/contracts.ts,components/O7FixturePreviewPanel.vue}`；`pc-tools/workstation/test/{catalog.test.ts,App.test.ts}`；`docs/interfaces/{o6_cloud_archive_api.md,o7_cloud_archive_task_api.md}`；`docs/product/pc_tools_workstation.md`；本 sprint `artifacts/full-stack/{fixture_live_camera_keyframe_annotation_material.json,o6_archive_write_receipt.json,o6_archive_readback.json,o7_consumer_readback.json,full_stack_validation.log}`。
- Product 后续：本 sprint `side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`；规划阶段不预生成。

## Algorithm 方案、live gate 和二进制边界
- 离线 fixture 覆盖 canonical/兼容/多候选、wrong type、0 publisher、daemon drift、dependency/timeout/retry、stamp/layout/encoding/hash/unsafe/binary 泄漏；新增代码中文注释比例 `>20%`。
- 最多一次 SSH inventory：单 shell source ROS，export `ROS2CLI_NO_DAEMON=1`，记录 daemon pre/post，运行 bounded topic list/info 与 rclpy/Image import；不写远端文件、不启停 runtime。
- 首选 `/camera/image_raw`；否则只允许唯一兼容 `sensor_msgs/msg/Image` 且 publisher `>=1`；0/多候选/type mismatch/daemon drift 均 capture count 0。
- gate clean 后最多一次 capture SSH/subscription，收到第一帧即 shutdown；hard timeout 12s；失败也 count 1 且不 retry，只清理 helper-owned process，禁止 broad kill。
- binary 只进入本地受控 sink/canonical PNG，不打印、不 JSON/base64/API/UI 内联；不支持 encoding 或 layout/hash 失败不生成假图。

## Full-stack 方案
- 用 synthetic fixture 并行扩展既有 O6/O7 主路径与只读 card；live/fixture badge 必须区分，不新增 submit/export/control/任意文件读取/OSS fetch。
- hostile tests 覆盖绝对路径、URL/query、base64/data URL、raw array、hash/stamp/task/source-count 错误和危险 true。
- Algorithm manifest clean 后只消费同一 JSON metadata；O6/O7 bug 只本地修复同一 fixture/manifest，不要求 live 重采；新增代码中文注释比例 `>20%`。

## 验收命令
- 规划：`test -f sprints/2026.07.15_11-58_o7_live_camera_keyframe_annotation_flow/{pre_start.md,prd.md,tech-plan.md}`；按任务给定 pattern 执行 `rg -n`；`git diff --check -- sprints/2026.07.15_11-58_o7_live_camera_keyframe_annotation_flow`。
- Algorithm 离线：`python3 -m py_compile onboard/scripts/o7_live_camera_keyframe_capture.py`；`python3 -m unittest discover -s onboard/tests -p 'test_o7_live_camera_keyframe_capture.py' -v`；中文注释比例断言；required `rg`；scoped `git diff --check`。
- Algorithm live：helper `inventory --ssh-target root@192.168.1.11 --ssh-port 37878 --ros2cli-no-daemon --max-inventory-ssh-invocations 1` 最多一次；gate clean 后 `capture-one --max-single-frame-capture-invocations 1 --timeout-s 12` 最多一次；结构断言校验 JSON/PNG/hash/size/counts/deltas/false fields。
- Full-stack：`python3 -m py_compile` relay/tests；`python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay -v`；workstation `npm run test && npm run build && npm run lint`；四个 JSON receipt `json.tool`；required `rg`；精确文件 scoped `git diff --check`。

## Mission Objective 0、Product 收口和禁止重用
- 仅真实单帧 + PNG/hash/manifest + O6/O7 lineage clean 时 `current_run_artifact_delta=true`；fixture/inventory/partial 为 false。`external_artifact_delta=false`、`live_control_delta=false`、`user_action_delta=false` 固定，Mission Objective 0 未满足。
- Product 必核对：两个 Engineer 文件范围、invocation 无第二次、daemon/runtime/topic/control 零 mutation、media/manifest/O6/O7 lineage、fixture/live badge、redaction/binary hostile tests、实际改动/验证/失败修复/风险写入 `tech-done.md`。
- fixture-only/blocked 保持 O5 85%、O6/O7 93%、O1 94%、KR 不归档；clean 也不证明 RTC/video、visible content、privacy approval、production annotation/cloud/OSS、route/delivery/HIL/safe-to-control。
- 本 sprint 后 camera inventory、single-frame helper、manifest、O6 section、O7 card 和相同 fixture matrix 立即退役；下一轮只消费更强真实 annotation action/audit、获授权 RTC/video、production media 或长期多帧回灌，禁止 preflight/readback/export/status/browser/voice/packet/mock wrapper。
