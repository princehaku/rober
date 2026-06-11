# 2026-06-11 23:45 Live Evidence Status Recapture

## sprint_type

micro

## 设计边界

- 本轮目标是重新采集真实上位机当前 evidence 状态，并修复 camera service 运行形态。
- 允许调用 PC fixed proxy 的 summary、camera first-frame probe、radar proof refresh、
  map proof refresh、localize reset、Nav2 no-motion proof refresh 和 base stop。
- 禁止调用 `/api/base/manual`、发布 `/cmd_vel`、执行 NavigateToPose、调用 `/api/nav2/start`
  或放宽非 stop 运动 gate。
- 硬件资料入口已读 `docs/vendor/VENDOR_INDEX.md`；本轮只涉及 camera service、LiDAR/Nav2
  no-motion evidence 和 stop，不改变 WAVE ROVER UART 协议或运动映射。

## 实际结果

- 初始板端状态显示 `trashbot-upper-robot-api.service=active`，但
  `trashbot-local-webrtc-camera.service=inactive`；8088 由手工残留
  `local_webrtc_camera_smoke.py` 进程监听。
- 已停止手工 camera 进程，并通过 systemd 启动 `trashbot-local-webrtc-camera.service`。
  最终两个服务均为 `active`，8088 由 systemd 管理的 `pid=303723` 监听。
- 对 systemd 管理的 camera 进程发起真实 aiortc offer 后，仍返回 HTTP 503
  `first_frame_unreadable/first_frame_timeout`；`/health` 和 PC summary 均读回
  `source_first_frame_failed`、`source_readiness=first_frame_failed`、
  `source_failure_reason=first_frame_timeout`。
- PC fixed proxy 安全 recapture 结果：
  - summary before/after：HTTP 200，`safe_to_control=false`。
  - camera first-frame probe：HTTP 502 / remote 503，
    `capture_read_call_timeout`，`visible_content_proven=false`。
  - radar scan proof refresh：HTTP 200 / remote 200，`last_result_status=refreshed`；
    summary after `latest_scan_proof_fresh=true`，但 lifecycle stopped。
  - map proof refresh：HTTP 200 / remote 200，
    `last_result_status=map_once_artifact_metadata_observed`。
  - localize reset：HTTP 200 / remote 200，`last_result_status=refreshed`。
  - Nav2 no-motion proof refresh：HTTP 200 / remote 200，但
    `last_result_status=blocked_with_root_cause`。
  - base stop：HTTP 200 / remote 200，`status=stopped`，
    `evidence_capture_status=captured`。
- Nav2 latest root cause：`path_generated=false`、`path_point_count=0`、
  `planner_server_active=true`，blockers 为 `map_to_odom_not_observed`、
  `map_to_base_link_blocked_by_missing_map_to_odom`（`/tf_topic_missing`）、
  `base_link_to_laser_frame_not_observed` 和 `localization_not_ready_for_path_generation`。

## 验证结果

- 真实 SSH：`root@192.168.1.11 -p 37878` 可达。
- 真实服务：`trashbot-upper-robot-api.service=active`、
  `trashbot-local-webrtc-camera.service=active`。
- 临时 PC API：`PORT=18813 npm run api` 和 `PORT=18814 npm run api` 分别用于 fixed proxy
  recapture 和最终 summary，结束后已用 Ctrl-C 关闭。
- `node` 解析 artifacts 成功，短摘要见
  `sprints/2026.06.11_23-45_live_evidence_status_recapture/artifacts/10_recapture_summary.json`。
- `node -e ... JSON.parse(...)`：`02/03/07/09/10` 五个 JSON artifact 解析通过。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 实时图传可见内容仍未恢复，根因仍停在 `/dev/video1` 首帧失败。
- Nav2 path generation 本轮回到 TF/localization blocker，需要继续查 AMCL frame 参数、
  `tf_broadcast`、static lidar TF 启动时机和 collector 观测窗口。
- 非 stop 运动 gate 仍缺 external video、visible camera、wheel feedback nonzero 和
  LiDAR motion delta；本轮只发送 stop，不执行真实移动。
