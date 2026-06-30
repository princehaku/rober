# onboard sensor current diagnostics

sprint_type: micro

## 实际改动

- 修正 `onboard/scripts/local_webrtc_camera_smoke.py` 的 `/health` 当前状态优先级：同一个视频源当前首帧失败时，历史 `last_successful_frame` 不再把 `source_observed` 置为 true，避免 PC 看到“当前失败但已观察首帧”的矛盾材料。
- 新增 `onboard/scripts/test_local_webrtc_camera_smoke_health.py`，覆盖 DV20 UVC 当前 `first_frame_total_timeout` 且无其他占用时，health 必须返回 `source_first_frame_failed` / `uvc_no_frame_not_exclusive`。
- 扩展 `onboard/scripts/test_upper_robot_api_free_roam.py`，验证 LiDAR driver 诊断 JSON 的 nested `diagnosis.status` 会展平成 PC 可消费的 `diagnosis_status`，例如 `serial_open_but_no_bytes`。
- 更新 `docs/product/pc_tools_workstation.md`，同步本轮现场只读诊断结论：PC 地图普通用户用本页大地图和 `?view=map`，ROS2 配套建议 RViz2 / Foxglove；相机当前问题按 USB/UVC 无首帧处理，雷达按 WAVE ROVER/STC vendor 资料和 driver diagnostics 排查。
- 2026-06-30 19:42 CST 现场部署到上车端：备份旧文件到 `/root/rober/runtime/deploy_backups/sensor_diag_20260630_194247` 和 `/root/rober/runtime/deploy_backups/upper_api_sensor_diag_20260630_194532`；同步 `local_webrtc_camera_smoke.py`、`o1_lidar_lifecycle.sh`、`lidar_driver.py`、`upper_robot_api.py`；远端重建 `ros2_trashbot_hardware` 并重启 8088 相机服务、8787 upper API、LiDAR lifecycle。该部署未调用任何底盘 motion/control POST，LiDAR lifecycle 只使用 `/dev/ttyACM0`，明确不使用 `/dev/ttyS5` 或 `/cmd_vel`。
- 修正 `onboard/scripts/o1_lidar_scan_proof_collector.py`：雷达 status 的 `fresh_scan_proof_observed` 不再被当成 blocker；topic 读取从四路并发改为顺序读取，避免 ROS2 CLI discovery 抖动；短窗口读取失败但上车已有 fresh latest proof 时，保留 fresh proof 作为 fallback，避免把好 artifact 覆盖成坏材料。
- 修正 PC radar proof refresh 固定合同：`pc-tools/workstation/src/server/robotControlSummary.ts` 不再从刷新按钮请求 `start_runtime`，固定 body 改为 `timeout_s=12`，代理 timeout 预算调为 90 秒；雷达启动继续走独立 `/api/robot-control/radar/start`，proof refresh 只读已有 topic。
- 2026-06-30 20:36 CST 修正上车 `GET /api/free-roam/autonomy/latest`：该入口改为真正 artifact-only，只读 `free_roam_autonomy_latest.json`、LiDAR scan proof artifact 和 runtime snapshot，不再同步调用相机 `/health` 或完整 `radar_status()`；相机 readiness 在该入口保守标为 `deferred_to_camera_health_endpoint`，所以不会误放开建图，但自由移动仍保持安全确认后可启动。
- 2026-06-30 20:36 CST 为 8787 常用只读同步 handler 增加线程隔离，覆盖 radar/base/map/Nav2/free-roam latest/status、delivery latest 等，避免 PC summary 并发读取多个端点时某个慢文件或状态读取阻塞 aiohttp 事件循环。
- 补齐 ROS2 配套 RViz2 观察面：`onboard/src/ros2_trashbot_bringup/rviz/trashbot_nav.rviz` 新增 Nav2 local plan、global costmap、local costmap，只做工程观察，不加入 GoalTool；`test_launch_contract_static.py` 锁定 RViz2 只读观察 `/map`、`/scan`、TF、`/plan`、`/local_plan`、`/amcl_pose` 和 costmap。
- 更新 `docs/navigation/free_roam_autonomy.md`、`docs/navigation/fixed_route_workflow.md`、`docs/product/pc_tools_workstation.md`：明确普通用户继续使用 PC `7001` 大地图和 `?view=map`，RViz2 是本地工程排障工具，Foxglove 是后续 bridge 后的浏览器远程观察工具。
- 2026-06-30 21:15 CST 修正 PC `?view=map` 直达地图页：`RobotControlConsolePanel.vue` 增加直达地图模式 DOM 合同，`styles.css` 在该模式隐藏非地图卡片，只保留地图面板、缩放、刷新和 ROS2 配套说明，避免连接/卡点/手控卡片继续挤占地图画布。该改动只影响显示，不启动 ROS2/RViz2/Foxglove，不执行 Nav2，不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。
- 2026-06-30 21:15 CST 修正 8088 相机服务共享占用残留：`local_webrtc_camera_smoke.py` 会在 `/health` 清理没有 active peer 且 0 帧的 stale shared capture，并在最近 `first_frame_total_timeout` 后对 MJPEG 自动重试加短冷却，避免浏览器自动重试反复占住 `/dev/video1`。新增单测覆盖 stale capture 释放和首帧失败冷却。
- 更新 `docs/product/pc_tools_workstation.md`，明确“地图太小”的现场用法：普通用户打开 PC `7001/?view=map` 得到真正只看地图的大屏；ROS2 配套是 RViz2 本地工程观察 `/map`、`/scan`、TF、Nav2 path、AMCL 和 costmap，Foxglove 是 bridge 后的浏览器远程观察，不替代普通用户 PC 地图。

## 验证结果

- `python3 -m unittest onboard.scripts.test_local_webrtc_camera_smoke_health onboard.scripts.test_upper_robot_api_free_roam`：通过，6 tests。
- `python3 -m py_compile onboard/scripts/local_webrtc_camera_smoke.py onboard/scripts/test_local_webrtc_camera_smoke_health.py onboard/scripts/test_upper_robot_api_free_roam.py`：通过。
- `python3 -m unittest onboard.src.ros2_trashbot_hardware.test.test_lidar_driver_stubs`：通过，16 tests。
- `npm test -- --run App.test.ts`（`pc-tools/workstation`）：通过，1 file / 225 tests。
- `python3 -m unittest onboard.scripts.test_upper_robot_api_free_roam`：通过，6 tests；覆盖 latest 不调用相机 HTTP 或完整 radar status。
- `python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api_free_roam.py`：通过。
- `python3 -m unittest onboard.src.ros2_trashbot_bringup.test.test_launch_contract_static`：通过，22 tests；覆盖 RViz2 配套观察面和不包含 GoalTool。
- `python3 -m unittest onboard.scripts.test_local_webrtc_camera_smoke_health onboard.scripts.test_upper_robot_api_free_roam`：通过，9 tests；覆盖 camera health stale shared capture 释放、最近首帧失败冷却，以及 free-roam latest artifact-only。
- `python3 -m py_compile onboard/scripts/local_webrtc_camera_smoke.py onboard/scripts/test_local_webrtc_camera_smoke_health.py`：通过。
- `npm test -- --run App.test.ts`（`pc-tools/workstation`）：通过，1 file / 225 tests；覆盖 `?view=map` DOM 合同、1600% 直达地图、RViz2/Foxglove 配套说明和不触发运动接口。
- `git diff --check`：通过。
- 上车端 `python3 -m py_compile /root/rober/onboard/scripts/local_webrtc_camera_smoke.py /root/rober/onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_driver.py`、`bash -n /root/rober/onboard/scripts/o1_lidar_lifecycle.sh`：通过；`colcon build --symlink-install --packages-select ros2_trashbot_hardware`：通过，1 package finished。
- 上车端部署 `upper_robot_api.py`、RViz2 launch/config/test 和 bringup CMake 安装合同后：`python3 -m py_compile scripts/upper_robot_api.py src/ros2_trashbot_bringup/test/test_launch_contract_static.py` 通过；`python3 -m unittest src.ros2_trashbot_bringup.test.test_launch_contract_static` 通过，22 tests；`colcon build --symlink-install --packages-select ros2_trashbot_bringup` 通过，1 package finished。
- 上车端重启 8787 后，`GET /api/free-roam/autonomy/latest` 在 PC summary 并发读取时返回 `HTTP 200 time 0.019721`、`runtime_status=loaded`、`camera_status=deferred_to_camera_health_endpoint`、`radar_lifecycle=not_checked_by_free_roam_latest`、`runtime_scan_ready=True`、`free_move_start_ready=True`、`mapping_start_ready=False`、`mapping_missing=camera_first_frame_not_observed`、`sends_motion=False`、`publishes_cmd_vel=False`。
- RViz2 安装验证：`ros2 pkg prefix ros2_trashbot_bringup` 返回 `/root/rober/onboard/install/ros2_trashbot_bringup`，安装后的 `trashbot_nav.rviz` 命中 `Nav2 Local Plan`、`Nav2 Global Costmap`、`Nav2 Local Costmap`。
- PC 7001 summary 并发复验：`live_status=needs_wheel_rerun`，下一步仍是重跑图上路线并复验 wheel L/R；`map_current=True`、`radar_map=True`、`free_move=True`、`keyboard=True`、`nav2=goal_succeeded_wheel_feedback_not_proven`、`minimal_precheck=True`。
- 上车端相机 `/health`：`status=source_first_frame_failed`、`source_readiness=first_frame_failed`、`source_failure_reason=first_frame_total_timeout`、`source_diagnosis.status=uvc_no_frame_not_exclusive`、`not_exclusive=true`、`last_successful_frame=null`。
- 上车端 LiDAR driver diagnostics：`diagnosis.status=scan_published`，`bytes_read_total=314482`、`packet_count_total=9387`、`published_raw_packet_count=9387`、`published_scan_count=515`；`ros2 topic echo --once /lidar/raw_packet` 和 `/scan` 均成功返回。
- PC 7001 只读刷新：`POST /api/robot-control/radar/scan-proof/refresh` 观测到 `scan_once_observed=true`、`scan_hz_observed=true`、`raw_packet_once_observed=true`、`tf_observed=true`；`GET /api/robot-control/map/preview` 返回 `radar_overlay_status=loaded`、`radar_overlay_point_count=72`、`path_preview_status=path_preview_observed`、`robot_pose_status=map_pose_observed`。
- PC 7001 summary：`readback_summary.radar.status=radar_ready`、`driver_diagnostics_status=scan_published`、`readback_summary.map.radar_overlay_status=loaded`、`radar_overlay_point_count=72`；`live_closure_summary.side_blocker_ids` 已不再包含 `radar_map_points_wysiwyg`。
- 2026-06-30 20:10 CST 复验 PC 固定雷达刷新：`POST /api/robot-control/radar/scan-proof/refresh` 返回 `proxy_status=refresh_forwarded`、`last_result_status=refreshed`、`scan_once_observed=true`、`scan_hz_observed=true`、`raw_packet_once_observed=true`、`tf_observed=true`、`latest_scan_proof_fresh=true`、`blocked_reasons=[]`；同轮 `GET /api/robot-control/map/preview` 返回 `radar_overlay_status=loaded`、`radar_overlay_point_count=72`。
- 上车端重启 8088 后，相机 `/health` 返回 `source_not_probed/not_in_use/shared_captures={}`；触发 `/mjpeg` 后最近首帧失败进入冷却，HTTP 503 在约 0.1s 返回 `first_frame_recent_failure_cooldown`，随后 `fuser /dev/video1 /dev/video2` 无 owner。后续 backend probe 仍显示 OpenCV open ok 但 read timeout，v4l2/ffmpeg 无 kernel frame，结论是 DV20 UVC 当前无真实帧，不是页面独占。
- PC 7001 summary 复验相机口径：`source_first_frame_failed`、`source_readiness=first_frame_failed`、`source_diagnosis=uvc_no_frame_not_exclusive`、`source_usage=not_in_use`；自由移动、键盘、地图和雷达 WYSIWYG 仍按原门禁展示。

## 剩余风险

- 本轮没有发送任何 live 运动/control POST；Nav2 完整路线当前仍停在 `needs_wheel_rerun`，需要现场安全确认后重跑图上路线，并在同一个执行窗口复验 wheel L/R 非零。
- 相机不是页面独占，但仍未恢复真实首帧；需要现场检查 DV20 UVC 的 USB、摄像头输入或供电，必要时换 known-good UVC 复测。
- 雷达地图贴图已恢复为 WYSIWYG；PC summary 和 map preview 已按 driver diagnostics + map overlay 正确展示。后续仍可单独继续清理历史 scan proof 字段兼容，但本轮 fixed radar refresh 已返回 `blocked_reasons=[]`。
- RViz2 配置已部署并构建，但本轮未在带图形桌面的现场启动 RViz2；真实 RViz2 渲染效果仍取决于当前 ROS graph 是否发布 `/map`、`/scan`、TF、Nav2 path 和 costmap。
- PC `?view=map` 现在是真正只看地图的 CSS/DOM 模式，但本轮未用真实浏览器截图验收现场屏幕尺寸；已用 Vitest DOM 合同和 CSS 规则锁定。真实显示仍取决于浏览器窗口大小和 operator 是否打开 `http://<PC>:7001/?view=map`。
