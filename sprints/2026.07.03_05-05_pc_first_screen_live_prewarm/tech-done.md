# PC 首屏地图/图传预热 micro sprint

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `refreshInitialLiveSurfaces()`，页面挂载后立即并行读取 `GET /api/robot-control/map/preview` 和 `GET /api/robot-control/camera/mjpeg/status`。
  - 初次地图/图传预热不等待完整 `GET /api/robot-control/summary`，summary 返回后再接管 WASD gate、目标闭环和完整诊断。
  - 该预热只读，不启动雷达 lifecycle、Nav2、manual、keyboard、free-roam、建图 runtime、delivery、stop 或 `/cmd_vel`。
- `pc-tools/workstation/src/server/index.ts`
  - 将 summary 内 MJPEG relay overlay 的相机 health 辅助读取预算收紧为 `600ms`。
  - 避免 USB full-speed/首帧失败时，相机 health 慢响应串行拖慢普通 PC 首屏。
- `pc-tools/workstation/test/App.test.ts`
  - 更新地图预热后的 map preview 调用计数断言。
  - 保留“执行后地图刷新失败不误发车”和“雷达贴图只读刷新不启动运动”的测试覆盖。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 PC 首屏先预热地图/共享图传，再等待 summary 完整诊断的产品合同。

## 验证结果

- `npm test -- --run test/App.test.ts -t "map|camera|keyboard|plain"`：通过，148 passed / 89 skipped。
- `npm test -- --run test/robotControlSummary.test.ts`：通过，11 passed。
- `npm test -- --run test/App.test.ts`：通过，237 passed。
- `npm run build`：通过；Vite 仍提示单 chunk 大于 500kB，这是既有前端体积 warning。
- 本地服务已重启到 `HOST=0.0.0.0 PORT=7001 npm run api`，监听进程 `node 42785`，`curl http://127.0.0.1:7001/` 和 `/map` 均返回当前构建产物。
- 现场读回：
  - `GET /api/robot-control/map/preview?baseUrl=http://192.168.1.11:8787` 约 1 秒返回 `proxy_status=preview_forwarded`，地图图像存在，`robot_pose_status=map_pose_observed`，`path_preview_point_count=18`，目标点 `target={x:0.8,y:0.05,frame_id=map,source_index=17}`，`radar_overlay_status=loaded`，当前雷达点 `139`，来源点 `152`。
  - `GET /api/robot-control/camera/mjpeg/status?baseUrl=http://192.168.1.11:8787` 返回 `source_diagnosis_status=uvc_full_speed_usb_not_exclusive`、`camera_usb_speed=12M`、`camera_hardware_action_required=true`、`shared_preview_everyone_can_join=true`、`shared_preview_current_frame_visible=false`。
  - `POST /api/robot-control/base/manual` 以 `direction=forward`、`speed=0.04`、`duration_ms=240`、`command_mode=ros` 返回 `proxy_status=command_forwarded`、`remote_http_status=200`，同窗口 `feedback_during_motion_t1001_frame_count=80`，随后 `POST /api/robot-control/base/stop` 返回 `command_forwarded`。

## 剩余风险

- 图传当前仍未出真实帧，现场证据指向 USB `12M` full-speed/首帧失败，不是 PC 页面独占；需要换高速 USB 口/线或带供电 Hub 后再复测。
- 手控 HTTP/ROS/UART 链路已转发成功，但 `wheel_feedback_latest_raw_left/right` 仍为 `0/0`，不能声明 wheel raw L/R 非零或真实位移 HIL 通过。
- SSH `root@192.168.1.11 -p 7878` 可登录，但登录 shell 中 `ros2` 不在 PATH，`/opt/ros/humble/setup.bash` 依赖 `/root/setup.sh` 失败；当前 ROS2 状态主要通过上位机 API/runtime artifact 验证。
