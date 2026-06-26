# 2026.06.27 16:25 PC Free-Roam Start Ready And Radar WYSIWYG

sprint_type: micro

## 实际改动

- 真机通过 PC 固定代理启动 LiDAR lifecycle：`POST /api/robot-control/radar/start?baseUrl=http://192.168.1.11:8787` 返回 `lifecycle_forwarded`，`command_result.executed=true`、`ok=true`。
- 雷达 ROS2 runtime 已在真机发布 `/scan` 和 `/lidar/raw_packet`；`/api/radar/status` 读回 `lifecycle_running=true`、`latest_scan_proof_fresh=true`、`continuous_window_observed=true`。
- PC summary 新增 `safe_command_boundary.free_roam_autonomy_start_ready`，把“可以发起自动扫图 start”与“runtime 已经解锁发布运动”分开。
- PC 普通首屏自动扫图按钮改用 `free_roam_autonomy_start_ready` 叠加本地安全确认、地图记录、地图画面刷新、摄像头 ready 和停止兜底；不再要求 `cmd_vel_publish_enabled=true` 后才允许点击 start。
- 同步更新 `docs/product/pc_free_roam_mapping_design.md` 和 `docs/product/pc_tools_workstation.md`。

## 验证结果

- `npm run build`：通过。
- `npm run lint`：通过。
- `python3 -m unittest onboard.tests.test_upper_robot_api onboard.tests.test_local_webrtc_camera_smoke`：通过，59 tests。
- `git diff --check`：通过。
- 真机 `/api/radar/status`：`running=true`、`fresh=true`、`continuous=true`、`state=scan_once_hz_raw_packet_tf_observed`、`rate=14.288`。
- PC summary：`free_roam_autonomy=locked` 且 `free_roam_autonomy_start_ready=true`；这证明按钮不再被“已解锁才允许解锁”的循环卡住。

## 剩余风险

- 本轮没有直接发起 free-roam start 让小车移动；因为真实现场仍需要 operator 勾安全确认、地图记录启动和地图画面刷新后再由 PC 固定 start 触发。
- 当前雷达最近障碍约 `0.04m`，上车策略会把它作为启动后的原地避让/不直行依据；这不是 PC start 前置 blocker。
- 雷达 lifecycle 当前保持 running；如现场不需要继续扫图，后续可点固定 `停止雷达`。
