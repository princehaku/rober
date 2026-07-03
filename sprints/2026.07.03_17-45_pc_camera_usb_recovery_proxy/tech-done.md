# PC 相机 USB 恢复代理

## sprint_type

micro

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - 新增固定上位机端点 `POST /api/camera/usb-recovery`，只运行 `camera_usb_recovery_smoke.py`。
  - 请求体只允许 `/dev/videoN` 和 `skip_service/skip_reauthorize/skip_audio_unbind` 三个布尔开关，避免 PC body 变成任意 root 命令。
  - 恢复结果把脚本 returncode `2` 作为“恢复动作完成但仍无帧”的可读诊断返回 HTTP 200，方便 PC 页面展示根因。
  - 补强相机 probe/recovery 子进程超时边界：进程刚好在超时边界退出时不再因 `ProcessLookupError` 打断 API JSON 返回。
- `pc-tools/workstation/src/server/index.ts`
  - 新增 `POST /api/robot-control/camera/usb-recovery` 固定代理，只能转发到上位机 `/api/camera/usb-recovery`。
  - 回包固定暴露 no-motion 边界：不发布 `/cmd_vel`、不打开底盘 UART、不启动 Nav2/键盘/自由移动/建图 runtime、不提交 delivery、不 stop。
  - 顶层抬出 `usb_video_speed`、`usb_high_speed_observed`、`stream_failure_class`、`next_action_plain` 和 `opens_camera_for_recovery`，现场不需要解析完整 raw payload。
- `pc-tools/workstation/src/shared/contracts.ts`
  - health `api_routes` 同步列出 `/api/robot-control/camera/usb-recovery?baseUrl=<robot-api-base-url>`，避免现场只看 `/api/health` 时误判 route 未部署。
- `pc-tools/workstation/test/catalog.test.ts`
  - 增加 camera USB recovery proxy 回归测试，覆盖 body 白名单、固定 endpoint、no-motion flags 和危险字段扫描。
- `docs/product/pc_tools_workstation.md`
  - 同步 PC 固定相机 USB 恢复代理、上位机端点、恢复动作范围和 480M/0 字节 live 结论。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步建图/自由移动边界：相机恢复动作只影响相机首帧和建图视觉验收，不阻塞低速自由移动或 PC WASD。

## 验证结果

- 通过：`python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/camera_usb_recovery_smoke.py`
- 通过：`python3 -m unittest onboard.scripts.test_camera_usb_recovery_smoke`，2 tests passed。
- 通过：`npm test -- --run test/catalog.test.ts -t "camera USB recovery|camera MJPEG status is readonly"`，2 tests passed。
- 通过：`npm test -- --run test/catalog.test.ts -t "camera USB recovery|health"`，9 tests passed。
- 通过：`npm test -- --run test/catalog.test.ts`，188 tests passed。
- 通过：`npm run lint`。
- 通过：`npm run build`；Vite 仍输出既有 chunk 大小 warning，构建成功。
- 通过：上位机部署后 `trashbot-upper-robot-api.service` active，`GET http://192.168.1.11:8787/api/health` 返回 `status=ready`。
- 通过：PC 7001 live `POST /api/robot-control/camera/usb-recovery?baseUrl=http://192.168.1.11:8787` 返回 `proxy_status=recovery_forwarded`、`remote_http_status=200`、`status=streamon_failed`、`usb_video_speed=480M`、`usb_high_speed_observed=true`、`stream_failure_class=high_speed_zero_byte_no_frame`、`opens_camera_for_recovery=true`，且 `publishes_cmd_vel=false`、`opens_base_uart=false`、`starts_nav2=false`、`starts_keyboard=false`、`robot_control_executed=false`。
- 通过：PC 7001 最终运行态已重启为 PID `15774`，监听 `*:7001`；`GET /api/health` 返回 `workstation_host=0.0.0.0`、`workstation_port=7001`、`default_robot_api_base_url=http://192.168.1.11:8787`、`has_usb_recovery_route=true`。
- 通过：PC 7001 live 地图 preview 返回 `preview_forwarded`、`map_name=trashbot_map`、`robot_pose_status=map_pose_observed`、`path_preview_status=path_preview_observed`、`path_preview_point_count=18`、`route_target_visible=true`、`radar_overlay_status=loaded`、`radar_overlay_point_count=41`、`image_data_url_present=true`。
- 通过：PC 7001 live 前进/后退手控复验均返回 `proxy_status=command_forwarded`、`remote_http_status=200`、`base_command_mode=ros`、`feedback_mode=realtime`、`command_result_ok=true`、`stop_result_ok=true`、`manual_command_executed=true`、`auto_stop_executed=true`、`motion_signal_observed=true`、`motion_signal_source=imu_attitude_delta`。

## 剩余风险

- 相机仍未出帧：当前已排除页面独占和 USB full-speed 低速口，真实 live 结果是 `480M` high-speed 但 STREAMON 仍 0 字节。下一步需要检查 USB 线/口/供电，或换 known-good UVC 设备复测。
- WASD/点动已有同窗口 IMU 运动信号，但 vendor `T=1001` wheel raw `L/R` 仍为 `0/0`，不能宣称 wheel raw 非零、完整 Nav2 路线 HIL 或 delivery success。
- 地图大屏当前 live 代理已证明地图、路线、目标点、机器人位姿和雷达点都可读；现场如果仍觉得画面太小，普通用户优先打开 `http://<PC>:7001/map`，ROS2 配套只作为工程观察使用 RViz2/Foxglove。
