# PC WASD mode readback

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`：`baseManualMotionKeyValues()` 新增 `base_command_mode`、`feedback_mode`、`command_result_ok`、`stop_result_ok`，让 PC WASD/低速点动回包直接显示本次底盘命令链路和 auto-stop 结果。
- `pc-tools/workstation/test/catalog.test.ts`：补充 first-jog 和 base/manual 两条代理测试，断言新字段会进入 `remote_motion_key_values`，同时保留 wheel raw L/R 与 IMU 运动信号的分离验收。
- `docs/product/pc_tools_workstation.md`：同步 PC 工作站产品合同。协议依据采用 `docs/vendor/VENDOR_INDEX.md` 指向的 WAVE ROVER UART JSON：`T=11` 是 direct PWM input，`T=13` 是 ROS control 且需要硬件确认；PC 默认仍用 ROS `/cmd_vel` 入口，由上车 bridge 映射到底盘兼容链路。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "first-jog proxy exposes raw during-motion|base manual proxy exposes IMU motion signal"`，1 file passed，2 tests passed。
- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts`，1 file passed，187 tests passed。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`；Vite 仍提示单个 chunk 超过 500 kB，这是既有体积 warning，本轮没有新增 build error。
- 已重启 PC Node：`HOST=0.0.0.0 PORT=7001 ROBOT_API_BASE_URL=http://192.168.1.11:8787 npm run api`，监听 `*:7001`，health 读回 `workstation_host=0.0.0.0`、`workstation_port=7001`、`default_robot_api_base_url=http://192.168.1.11:8787`。
- Live 地图读回：`GET /api/robot-control/map/preview` 返回 `proxy_status=preview_forwarded`、`image_data_url_present=true`、`map_name=trashbot_map`、`robot_pose_status=map_pose_observed`、`path_preview_point_count=18`、`route_target_visible=true`、`target={x:0.8,y:0.05}`、`radar_overlay_status=loaded`、`radar_overlay_point_count=64`，且 `sends_motion_when_clicked=false`。
- Live 相机读回：`GET /api/robot-control/camera/mjpeg/status` 返回 `shared_capture=true`、`shared_preview_everyone_can_join=true`、`exclusive_camera_claim=false`、`camera_usb_speed=480M`，但 `status=source_first_frame_failed`、`source_diagnosis_status=uvc_no_frame_not_exclusive`。
- Live 手控读回：`POST /api/robot-control/base/manual` 低速 `forward` 320ms 返回 `proxy_status=command_forwarded`、`base_command_mode=ros`、`feedback_mode=realtime`、`command_result_ok=true`、`stop_result_ok=true`、`manual_command_executed=true`、`auto_stop_executed=true`、`feedback_during_motion_t1001_frame_count=80`、`motion_signal_observed=true`、`motion_signal_source=imu_attitude_delta`。

## 剩余风险

- 同轮手控 `wheel_feedback_latest_raw_left=0`、`wheel_feedback_latest_raw_right=0`，`wheel_feedback_lr_nonzero_proven=false`；本轮只证明 PC/API/上车 command/stop 与运动信号读回，没有证明 WAVE ROVER wheel raw L/R 非零。
- 相机不是页面独占，且共享预览允许多人加入；但 UVC 源仍没有首帧，实时画面 WYSIWYG 未完成。
- `delivery_success=false`，完整 Nav2 路线真实移动闭环仍需要同窗口 wheel raw L/R 非零和送达确认。
