# PC map 800% ROS2 companion

sprint_type: micro

## 实际改动

- 将 PC 普通首页和 `/map` 默认地图缩放从 `300%` 调整为 `800%`，`完整态势` 保持回到 `100%`，`细节放大` 最高保持 `4800%`。
- 同步更新 `summary/live-summary` 合同、DOM data 属性、Vitest 断言和 catalog 断言，确保 `map_display_default_zoom_percent` 与 `map_display_direct_map_default_zoom_percent` 都返回 `800%`。
- 保持 ROS2 配套的产品分层：普通用户继续使用 PC 大地图和 `/map`；RViz2/Nav2 RViz 配置与 Foxglove bridge + Foxglove Web 只作为工程观察入口，不替代简易控制台，不发送运动命令。
- 同步更新 `docs/product/pc_tools_workstation.md`、`docs/process/okr_progress_log.md` 和 `OKR.md` 的当前地图显示口径。

## 验证结果

- `cd pc-tools/workstation && npm test -- test/robotControlSummary.test.ts --run`：通过，18 tests OK。
- `cd pc-tools/workstation && npm test -- test/App.test.ts --run`：通过，242 tests OK。
- `cd pc-tools/workstation && npm test -- test/catalog.test.ts --run`：通过，195 tests OK。
- `cd pc-tools/workstation && npm run build`：通过；Vite 仍提示单个 chunk 超过 500 kB，这是既有打包体积警告，不影响本轮构建。
- 本机 PC Node 已重启并继续监听 `0.0.0.0:7001`；`GET /api/health` 返回 `workstation_port=7001`、`default_robot_api_base_url=http://192.168.1.11:8787`。
- 重启后 `GET /api/robot-control/live-summary?baseUrl=http://192.168.1.11:8787` 返回 `status=ready_for_motion`、`map_display_default_zoom_percent=800%`、`map_display_direct_map_default_zoom_percent=800%`、`map_display_fit_zoom_percent=100%`、`map_display_max_zoom_percent=4800%`、`map_display_ros2_companion_tools=[rviz2,foxglove]`。
- 真实 7001 手控复验：`POST /api/robot-control/base/manual` 低速 `forward` 返回 `proxy_status=command_forwarded`、`command_raw_lr_nonzero_proven=true`、`command_raw_latest_left/right=164/164`；低速 `backward` 返回 `command_raw_latest_left/right=-164/-164`；两次 `POST /api/robot-control/base/stop` 均返回 `proxy_status=command_forwarded`，随后 live-summary 返回 `keyboard_continuous_forwarded_pulses=2`、`keyboard_stop_settled_after_pulse=true`。
- 真实 7001 自由移动复验：`POST /api/robot-control/free-roam/autonomy/start` 携带 `confirm_operator_safety=true` 返回 `proxy_status=autonomy_forwarded`、`sets_state_machine_parameters=true`、`motion_unlock_requested=true`、`latest_decision_state=avoiding`；`GET /api/robot-control/free-roam/autonomy/latest` 返回 `free_roam_motion_ready=true`；随后 `POST /api/robot-control/free-roam/autonomy/stop` 返回 `proxy_status=autonomy_forwarded`，停稳后 latest 返回 `free_roam_motion_ready=false`。
- 相机共享预览复验：`GET /api/robot-control/camera/mjpeg/status` 返回 `shared_preview_everyone_can_join=true`、`shared_preview_exclusive_camera_claim=false`、`source_usage_owner_count=0`、`source_diagnosis_status=uvc_no_frame_not_exclusive`、`last_remote_http_status=503`，说明 PC 页面不是独占者；当前 DV20 UVC 源仍未输出首帧。

## 剩余风险

- 本轮主要调整 PC 地图显示比例和工程观察口径；追加现场复验证明 WASD/手控命令和自由移动 start/stop 可用，但不修复真实相机无帧、wheel raw `T=1001 L/R=0/0` 或完整路线长期 HIL。
- 自由移动 start 后进入 `avoiding`，与当前雷达近障约 `0.04m` 的现场状态一致；若要长期自动行驶，需要现场留出前方距离后继续跑完整窗口，或再设计更明确的近障原地转向策略。
- `800%` 默认会让小地图细节更大，但用户若需要全局态势仍应点击 `完整态势` 回到 `100%`。
