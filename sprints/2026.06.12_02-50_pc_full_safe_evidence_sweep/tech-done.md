# 2026.06.12 02:50 PC Full Safe Evidence Sweep

## sprint_type

micro

## 实际改动

- 新增本轮真实 PC fixed proxy 安全总巡检 artifact，路径：
  `sprints/2026.06.12_02-50_pc_full_safe_evidence_sweep/artifacts/`。
- 本轮不调用 subagent，不改产品代码，不改 PC 普通用户简易首屏，不改硬件配置。
- 巡检通过本机 PC API 代理访问真实上位机 `http://192.168.1.11:8787`，覆盖 summary、camera
  first-frame probe、radar start/refresh/stop、map list/refresh、localize reset、Nav2
  no-motion proof refresh、base feedback samples 和 base stop。
- 巡检未调用 `/api/base/manual` 成功路径，未发布 `/cmd_vel`，未执行 NavigateToPose，未写
  WAVE ROVER UART `/dev/ttyS5`。
- 同步更新：
  - `docs/product/pc_tools_workstation.md`
  - `docs/vision/board_camera_publisher.md`
  - `docs/navigation/fixed_route_workflow.md`
  - `docs/hardware/board_sensor_stack_smoke.md`

## 验证结果

- JSON artifact 校验：15 个 `.json` 全部可解析。
- 巡检关键结果：
  - PC summary before/after：`console_status=loaded_fail_closed_summary`，
    `robot_api_connection.status=readable`，危险字段为空。
  - Camera：PC proxy first-frame probe 返回 HTTP 503，
    `status=first_frame_timeout`，`failure_reason=capture_read_call_timeout`，
    `open_ok=true`，`read_ok=false`，backend smoke 为 `backend_no_frame_observed`。
  - Radar：`radar/start` 与 `radar/stop` 均通过固定 lifecycle 代理转发；
    `radar/scan-proof/refresh` 返回 HTTP 200，`scan_once_observed=true`、
    `scan_hz_observed=true`、`raw_packet_once_observed=true`、`tf_observed=true`，
    证据号 `o1-lidar-scan-proof-1781187807175`。
  - Map：`map/proof/refresh` 返回 HTTP 200，读到
    `map_once_artifact_metadata_observed`，证据号 `o3-map-lifecycle-1781183225157`。
  - Localization：`localize/reset` 固定代理返回 HTTP 200，但结果为
    `blocked_with_root_cause`；`initialpose_published=true`，
    `amcl_pose_observed=false`，`managed_runtime_cleanup_ok=false`。
  - Nav2：`nav2/proof/refresh` 固定代理返回 HTTP 200，但结果为
    `blocked_with_root_cause`；`planner_server_active=true`，
    `path_generated=false`，`path_point_count=0`。
  - Base feedback：固定只读采样代理返回 HTTP 200，3/3 样本观测到 `T=1001`，
    `feedback_ack_t1001_observed=true`，`sends_motion_commands=false`。
  - Base stop：固定 stop 代理返回 HTTP 200，`status=stopped`。
- 收尾复核：`trashbot-upper-robot-api.service` 与
  `trashbot-local-webrtc-camera.service` 均为 active；`/dev/ttyS5`、`/dev/ttyACM0`、
  `/dev/video0`、`/dev/video1`、`/dev/video2` 未观察到额外 holder 输出。

## 剩余风险

- 这轮只证明 PC 能安全触发和读取当前 fixed proxy 证据链，不证明真实手动移动、
  NavigateToPose、controller 执行、路线巡航、HIL pass 或 delivery success。
- Camera 仍卡在 DV20 `/dev/video1` 首帧 timeout；PC 实时图传可见内容未恢复。
- Radar 本轮能采到 scan/raw/tf 一次性 proof，但 lifecycle running 时
  continuity readback 仍出现 `latest_proof_stale_while_lifecycle_running`。
- Localization/Nav2 在本次 full sweep 中从前一轮成功状态回落为 blocked；需要继续查
  managed runtime cleanup、AMCL pose、TF 观测窗口和 planner/costmap 稳定性。
- PC 对 localize root causes 的高级摘要仍把对象压成 `[object Object]`，证据可判读但不够友好；
  后续可单独改善 root cause 展示。
