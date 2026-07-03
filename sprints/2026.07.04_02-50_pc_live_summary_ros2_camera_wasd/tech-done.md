# PC live-summary 地图别名、ROS2 配套复核、相机/WASD 现场证据

## sprint_type

micro

## 实际改动

- `GET /api/robot-control/live-summary` 增加 `route_target_current_visible`、`radar_map_points_current_visible`，PC summary 顶层同步增加相同别名，便于现场脚本直接验收地图、Nav2 路线、目标点和雷达点是否都在当前画布。
- 更新 `RobotControlSummaryResponse` / `RobotControlLiveSummaryResponse` 类型和 `robotControlSummary` 单元测试，锁定上述别名。
- 更新 `docs/product/pc_tools_workstation.md` 与 `docs/product/pc_free_roam_mapping_design.md`：记录 2026-07-04 02:50 CST 的真实地图、ROS2 配套、相机和 WASD 证据。
- 2026-07-04 03:05 CST 追加修复 `GET /api/robot-control/base/status` 独立只读代理：允许
  `bridge_command_debug.robot_control_executed=true` 作为历史命令 debug 材料，不再让当前只读 GET 返回 502；
  新增 catalog 路由级回归测试。
- 同步更新产品文档：记录本轮 `base/status` live 200、PC 手控命令 raw 非零、IMU 动作信号可见，以及
  `T=1001 L/R=0/0` 和 DV20 V4L2 0 字节的剩余风险。
- 2026-07-04 03:20 CST 追加 PC 地图易用性修正：普通首页和 `/map` 默认缩放从 `150%` 提升到
  `200%`，地图面板和内层 WYSIWYG 画布增高，顶栏入口改为 `地图大屏 /map`；ROS2 配套继续只作为
  `工程观察：RViz2 / Foxglove`，不替代普通用户简易控制台。
- 2026-07-04 04:05 CST 继续响应“PC 地图太小 / ROS2 配套”反馈：普通首页和 `/map` 默认缩放从
  `200%` 提升到 `300%`，`完整态势` 仍回 `100%`，`细节放大` 仍到 `1200%`；summary/live-summary、
  Vue DOM 和类型合同同步更新。ROS2 配套口径保持：RViz2/Nav2 RViz 插件用于本地工程调试，Foxglove
  bridge + Foxglove Web 用于远程浏览器观察，普通用户继续使用 PC 大地图和 `/map`。
- 2026-07-04 03:53 CST 追加 Nav2 执行模式读回修正：`o11_nav2_goal_execution_proof.py`
  在复用现场已有 ROS/Nav2/`esp32_bridge` runtime 时写出 `requested_base_command_mode`、
  `base_command_mode_matches_request` 和 `base_command_mode_mismatch_reused`，避免 PC 请求 ROS 复验但实际复用
  PWM bridge 时被误读成“ROS 已切换”；PC `nav2/goal/execution/latest` 与 summary/live-summary 均优先采用
  上位机 `next_base_command_mode`，不再自行把 PWM wheel-zero 推断成下一轮 ROS。
- PC Node 键盘本地证据缓存从 2 分钟延长到 10 分钟；它仍只保存本机代理刚发出的手控/stop 材料，不跨 Node 重启，
  但能覆盖一次现场测试、构建和文档更新的验收窗口，避免 WASD stop 证据在同轮收口前自然过期。
- 新增 `onboard/scripts/test_o11_nav2_goal_execution_proof.py`，锁定“请求 ROS、实际 PWM 复用必须标记 mismatch”的轻量合同。

## 验证结果

- 已通过：`npm test -- --run test/robotControlSummary.test.ts`，`16 passed`。
- 已通过：`npm test -- --run test/App.test.ts -t "map"`，`70 passed`。
- 已通过：`npm test`，`3 passed`、`447 passed`。
- 已通过：`npm run build`；仅有既有 Vite chunk size warning。
- 上位机 ROS2 配套复核已通过：`ros2 pkg prefix ros2_trashbot_bringup` 返回 `/root/rober/onboard/install/ros2_trashbot_bringup`；`foxglove_bridge.launch.py --show-args` 返回 `address=0.0.0.0`、`port=8765`、`use_sim_time=false`、`sysinfo=true`；`rviz.launch.py --show-args` 返回 `rviz/trashbot_nav.rviz`。
- live 读回：`map_current_visible=true`、`path_current_visible=true`、`route_target_visible=true`、`route_target_current_visible=true`、`radar_map_points_current_visible=true`、`radar_overlay_current_point_count=190`、`map_display_default_zoom_percent=150%`、`map_display_direct_map_default_zoom_percent=150%`。
- WASD/方向键链路复验：PC 发前进、停止、后退、停止后，`live-summary` 读回 `keyboard_motion_verified=true`、`keyboard_stop_settled_after_pulse=true`、`keyboard_command_raw_lr_nonzero_proven=true`、`keyboard_motion_evidence_complete=true`。
- 相机复验：PC 共享 MJPEG 返回 502；首帧探针返回 `open_failed`/503；USB recovery 返回 `stream_failure_class=high_speed_zero_byte_no_frame`；上位机直接 `v4l2-ctl` 对 `/dev/video1` 的 MJPG/YUYV 采帧均 `select timeout` 且输出 0 字节。
- 已通过：`npm test -- --run test/catalog.test.ts -t "base status proxy"`，`1 passed`。
- 已通过：`npm test -- --run test/App.test.ts -t "map"`，`70 passed`，确认当前默认地图缩放和
  `/map` 直达页合同均为 `200%`。
- 已通过：`npm test -- --run test/robotControlSummary.test.ts`，`16 passed`。
- 已通过：`npm test -- --run test/catalog.test.ts -t "live-summary"`，`1 passed`。
- 已通过：`npm test`，`3 passed`、`448 passed`。
- 已通过：`npm run build`；仍只有既有 Vite chunk size warning。
- PC Node 已重启到 `0.0.0.0:7001`，PID `64214`；实际 `summary` / `live-summary`
  读回 `map_display_default_zoom_percent=200%`、`map_display_direct_map_default_zoom_percent=200%`，
  且 `map_display_starts_ros2=false`、`map_display_starts_nav2=false`、`map_display_sends_motion_when_clicked=false`。
  当前 live 仍显示地图、路线、目标点和雷达点可见，相机首帧仍不可见。
- 2026-07-04 03:34 CST 追加现场验证：雷达只读刷新后 `map/preview` 返回
  `robot_pose_status=map_pose_observed`、`path_preview_point_count=18`、`route_target_visible=true`、
  `radar_overlay_status=loaded`、`radar_overlay_current_point_count=70`。PC `command_mode=ros`
  前进/后退短脉冲均 `proxy_status=command_forwarded`、`command_raw_lr_nonzero_proven=true`、
  `motion_signal_observed=true`、`stop_result_ok=true`；live-summary 随后读到
  `keyboard_motion_verified=true`、`keyboard_stop_settled_after_pulse=true`。上车 `esp32_bridge`
  参数为 `command_mode=pwm`、`command_transport=http`、`wave_rover_http_base_url=http://192.168.1.3`、
  `main_type=2`、`module_type=0`、`pwm_min_abs=255`、`pwm_max_abs=255`，command debug 记录
  vendor `T=11 L/R=±255` 与 stop `T=11 L/R=0`。speed 模式本轮未观察到运动信号。
- 相机追加验证：`/dev/video1` 是 DV20 UVC video capture，`/dev/video2` 是 metadata，USB 为 `480M` 且无人占用；
  PC MJPEG 仍返回 `first_frame_total_timeout`，USB recovery 后 `stream_failure_class=high_speed_zero_byte_no_frame`；
  停止相机服务后独占直采 `YUYV@320x240` 和 `MJPG@640x480` 各 30 秒均 0 字节，服务已恢复到 8088。
  当前相机缺口不在 PC 页面、共享预览、浏览器独占或短超时。
- live 修复复验：PC Node PID `42460` 监听 `0.0.0.0:7001`；`GET /api/robot-control/base/status`
  返回 HTTP 200、`proxy_status=status_loaded`、`blocked_reasons=[]`、`hard_dangerous_true_fields=[]`、
  `wheel_feedback_lr_nonzero_proven=false`，且当前采样窗口已读到 `T=1001`。
- 同轮手控复验：PC `POST /api/robot-control/base/manual` 前进/后退返回 HTTP 200、`proxy_status=command_forwarded`、
  `command_raw_lr_nonzero_proven=true`、`motion_signal_observed=true`、`motion_signal_source=imu_attitude_delta`，
  但 `wheel_feedback_lr_nonzero_proven=false`、`wheel_feedback_latest_raw_left/right=0/0`。
- Vendor 反馈复核：依据 `docs/vendor/VENDOR_INDEX.md`、`json_cmd.h`、`movtion_module.h` 与 `ugv_advance.h`，
  `T=1001.L/R` 来自固件 `speedGetA/B`；现场发 `{"T":900,"main":1,"module":0}` 后，PC 低速 PWM 手控仍未读到非零 L/R。
- 相机补充复验：`/dev/video1` 无 owner、USB 为 `480M`，但直连 `v4l2-ctl` 的 MJPG/YUYV 仍 `select timeout` 且 0 字节；
  `8088/mjpeg` 多格式返回 `opencv_capture_not_opened`。
- 2026-07-04 03:53 CST 本轮验证：
  - 已通过：`python3 -m py_compile onboard/scripts/o11_nav2_goal_execution_proof.py onboard/scripts/test_o11_nav2_goal_execution_proof.py`。
  - 已通过：`python3 onboard/scripts/test_o11_nav2_goal_execution_proof.py`，`2 passed`。
  - 已通过：`npm test -- --run test/robotControlSummary.test.ts`，`16 passed`。
  - 已通过：`npm test -- --run test/catalog.test.ts`，`191 passed`。
  - 已通过：`npm run build`；仍只有既有 Vite chunk size warning。
- 部署验证：已将 `o11_nav2_goal_execution_proof.py` 部署到上位机 `/root/rober/onboard/scripts/`，`python3 -m py_compile`
  通过；`trashbot-upper-robot-api.service` 重启时旧进程卡在 `stop-sigterm`，已用 systemd SIGKILL 恢复后重新启动，
  8787 health 返回 `status=ready`。
- 现场 Nav2 复测：PC 以 `base_command_mode=ros` 执行当前图上目标 `{x:0.8,y:0.05,frame_id:map}`，
  返回 `proxy_status=execution_forwarded`、`goal_status=goal_succeeded`、`result_status=succeeded`、
  `requested_base_command_mode=ros`、实际 `base_command_mode=pwm`、
  `base_command_mode_matches_request=false`、`base_command_mode_mismatch_reused=true`、
  `base_command_nonzero_observed=true`、`base_command_nonzero_count=1076`、
  `base_feedback_lr_nonzero_proven=false`、`L/R=0/0`、`imu_delta=true`。
- PC 7001 已重启，PID `88289` 监听 `0.0.0.0:7001`；`/api/robot-control/nav2/goal/execution/latest`
  与 summary/live-summary 已读回 `next_execution_base_command_mode=pwm`、`wheel_rerun_next_base_command_mode=pwm`、
  `goal_execution_next_mode_plain=下次继续用 PWM 模式重跑图上路线。`
- 同轮现场状态复验：`map_current_visible=true`、`path_current_visible=true`、
  `route_target_current_visible=true`、`radar_map_points_current_visible=true`、`radar_overlay_current_point_count=92`；
  PC 前进/后退短脉冲均 `proxy_status=command_forwarded`、`command_raw_lr_nonzero_proven=true`、
  `motion_signal_observed=true`、`stop_result_ok=true`，live-summary 读回
  `keyboard_motion_verified=true`、`keyboard_command_raw_lr_nonzero_proven=true`、`keyboard_stop_settled_after_pulse=true`。
- 相机同轮只读复测：`POST /api/robot-control/camera/first-frame/probe` 返回
  `proxy_status=probe_failed`、`status=probe_total_timeout`、HTTP 503、`camera_first_frame=false`、
  `usb=480M`；live-summary 归类 `camera_source_diagnosis_status=uvc_no_frame_not_exclusive`、
  `camera_source_diagnosis_not_exclusive=true`，继续说明“已排除页面独占和低速 USB；设备没有输出视频帧”。
- TTL 调整后最终复验：PC Node PID `91447` 监听 `0.0.0.0:7001`；再次执行前进/停止/后退/停止后，
  live-summary 稳定读回 `map_current_visible=true`、`path_current_visible=true`、
  `route_target_current_visible=true`、`radar_map_points_current_visible=true`、
  `keyboard_motion_verified=true`、`keyboard_command_raw_lr_nonzero_proven=true`、
  `keyboard_stop_settled_after_pulse=true`、`camera_current_visible=false`、
  `camera_source_diagnosis_status=uvc_no_frame_not_exclusive`、`wheel_lr_nonzero_proven=false`、
  `wheel_rerun_next_base_command_mode=pwm`、`delivery_success=true`。
- 2026-07-04 04:05 CST 地图放大与 ROS2 配套复验：
  - 已通过：`npm test -- --run test/App.test.ts -t "map"`，`70 passed`。
  - 已通过：`npm test -- --run test/robotControlSummary.test.ts`，`16 passed`。
  - 已通过：`npm test -- --run test/catalog.test.ts -t "map_display|live-summary|base status proxy"`，`2 passed`。
  - 已通过：`npm test`，`448 passed`。
  - 已通过：`npm run build`；仍只有既有 Vite chunk size warning。
  - PC Node 已重启到 `0.0.0.0:7001`，PID `4404`；summary/live 读回
    `map_display_default_zoom_percent=300%`、`map_display_direct_map_default_zoom_percent=300%`、
    `map_display_fit_zoom_percent=100%`、`map_display_max_zoom_percent=1200%`。
  - 只读刷新雷达 proof 和 map preview 后，当前 summary 读回 `map_current_visible=true`、
    `map_preview_status=loaded`、`path_preview_point_count=18`、`route_target_visible=true`、
    `radar_map_points_visible=true`、`live_wysiwyg_radar_map_current_point_count=126`，
    且 `map_display_starts_ros2=false`、`map_display_starts_nav2=false`、
    `map_display_sends_motion_when_clicked=false`。

## 剩余风险

- 实时图传仍未出首帧。当前证据排除了 PC 页面、多人预览独占和 Node relay，剩余指向 DV20 摄像头输入、USB 线/接口/供电或设备本体；需要现场硬件动作后复测。
- Vendor `T=1001 L/R` 仍为 `0/0`，wheel raw L/R 非零闭环未完成。当前只能证明 PC 键盘命令已发出、stop 已落稳、命令 raw 非零和 IMU/运动信号存在，不能宣称完整 wheel raw 或完整自动驾驶闭环完成。
- Nav2 现在能清楚区分“请求模式”和“实际 runtime 模式”：本轮请求 ROS 但因复用现场 PWM `esp32_bridge`，实际仍按 PWM/T=11
  路径完成 goal。后续若必须做 ROS/T=13 复验，需要先处理现有 runtime/串口 owner 的切换策略，不能在已有 bridge 持有链路时假装模式已切。
- 裸串口并发读 `/dev/ttyS5` 会撞到 `device disconnected or multiple access on port?`；后续复验应继续走
  bridge/API 的固定读回链路，不绕开现有串口 owner 抢读。

## 2026-07-04 04:30 CST 追加修复与验证

- 修复 PC `POST /api/robot-control/camera/first-frame/probe` 的诊断聚合：当上车 health 仍是
  `source_selected_not_probed`，但本次 probe 已返回 `probe_total_timeout`、多格式 fallback 和低带宽组合均无首帧时，
  PC 代理现在直接返回 `source_diagnosis_status=uvc_no_frame_not_exclusive`、
  `source_diagnosis_not_exclusive=true`、`camera_hardware_action_label=检查摄像头输入/供电后复测`，
  不再把普通页面降级成“复测相机首帧”或误导为页面独占。
- 新增/更新测试覆盖：
  - `npm test -- --run test/catalog.test.ts -t "workstation camera first-frame probe uses quick source check"`：通过，`1 passed`。
  - `npm test -- --run test/catalog.test.ts -t "camera first-frame probe|camera mjpeg|uvc_no_frame|source_first_frame"`：通过，`4 passed`。
  - `npm test -- --run test/robotControlSummary.test.ts -t "camera|first frame|mjpeg|uvc_no_frame"`：通过，`4 passed`。
  - `npm test`：通过，`448 passed`。
  - `npm run build`：通过；仍只有既有 Vite chunk size warning。
- PC Node 已重启到 `0.0.0.0:7001`，当前监听 PID 为 `15404`。真实上位机复测：
  - `POST /api/robot-control/camera/first-frame/probe` 返回 `proxy_status=probe_failed`、
    `status=probe_total_timeout`、HTTP 503、`frame_observed=false`、`usb=480M`、
    `source_diagnosis_status=uvc_no_frame_not_exclusive`、`camera_hardware_action_required=true`。
  - 顺序刷新后的 `GET /api/robot-control/live-summary` 返回 `map_current_visible=true`、
    `path_current_visible=true`、`radar_map_points_visible=true`、`camera_current_visible=false`、
    `camera_source_diagnosis_status=uvc_no_frame_not_exclusive`、`camera_input_signal_check_required=true`、
    `delivery_success=true`、`keyboard_continuous_motion_verified=true`、`wheel_lr_nonzero_proven=false`。
- 再次低速手控复验：PC 通过固定 `/api/robot-control/base/manual` 发 `pwm` 前进/后退 700ms，均返回
  `proxy_status=command_forwarded`、`command_raw_lr_nonzero_proven=true`，stop 返回 `command_forwarded`。
  后续 `/api/robot-control/base/feedback-samples` 仍为 `wheel_feedback_lr_nonzero_proven=false`、
  vendor `T=1001 L/R=0/0`。SSH 上位机确认 `/dev/ttyS5` 的唯一持有者是 `esp32_bridge`；
  command debug 记录 manual `T=11 L/R=±164` 和历史 Nav2 bridge `T=11 L/R=±255` 均写出成功，
  feedback debug 连续 `T=1001` 仍回 `L=0,R=0`。依据 `docs/vendor/VENDOR_INDEX.md`，
  `T=1001.L/R` 是 WAVE ROVER 固件反馈字段；因此 wheel raw L/R 非零闭环仍未完成，不能把完整自动驾驶验收标为完成。

## 2026-07-04 04:45 CST 地图太小跟进

- PC 普通首页和 `/map` 直达页默认缩放继续从 `300%` 提升到 `400%`；`完整态势` 仍回 `100%`，
  `细节放大` 提升到 `1600%`。Vue DOM、CSS、summary/live-summary 和共享类型合同同步更新。
- `/map` 直达页去掉地图卡内边距，标题和工具条改成画布内顶部浮层，图层状态改成底部浮层；直达页标题文字隐藏，
  只保留缩放、刷新地图、刷新雷达贴图和工程观察折叠入口，避免工具行继续占用地图高度。
- ROS2 配套口径同步到产品文档：普通用户继续用 PC 大地图和 `/map`；本地工程调试用 RViz2/Nav2 RViz 配置；
  远程浏览器观察用 `foxglove_bridge` + Foxglove Web。工程观察入口仍固定只读，不启动 ROS2/RViz2/Foxglove/Nav2/
  建图 runtime，不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 验证通过：
  - `npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`，
    `1 passed`。
  - `npm test -- --run test/App.test.ts -t "map"`，`70 passed`。
  - `npm test -- --run test/robotControlSummary.test.ts`，`16 passed`。
  - `npm test -- --run test/catalog.test.ts -t "map_display|live-summary|base status proxy"`，`2 passed`。
  - `npm test`，`3 passed`、`448 passed`。
  - `npm run build` 通过；仍只有既有 Vite chunk size warning。
- PC Node 已重启并监听 `0.0.0.0:7001`，实际进程 PID `40622`；live-summary 读回
  `map_display_default_zoom_percent=400%`、`map_display_direct_map_default_zoom_percent=400%`、
  `map_display_fit_zoom_percent=100%`、`map_display_max_zoom_percent=1600%`，且
  `map_display_starts_ros2=false`、`map_display_starts_nav2=false`、`map_display_sends_motion_when_clicked=false`。
- 只读雷达 proof 刷新后，`/api/robot-control/map/preview` 返回 `path_preview_point_count=18`、
  `route_target_visible=true`、`radar_overlay_status=loaded`、`radar_overlay_current_point_count=167`；
  随后 live-summary 读回 `map_current_visible=true`、`path_current_visible=true`、
  `route_target_current_visible=true`、`radar_map_points_current_visible=true`、
  `live_wysiwyg_radar_map_current_point_count=167`。该刷新确认 `starts_radar_lifecycle=false`、
  `starts_nav2=false`、`robot_control_executed=false`。
