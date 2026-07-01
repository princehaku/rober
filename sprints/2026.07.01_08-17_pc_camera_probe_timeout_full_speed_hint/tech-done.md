# 相机 probe 超时保留 USB full-speed 根因

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `cameraProbePlainFailureHint()` 在首帧 probe 失败或代理超时时，优先消费 summary/MJPEG status 的 UVC USB 拓扑诊断。
  - 当已有 `uvc_full_speed_usb_not_exclusive`、`uvc_video_on_full_speed_usb` 或 `uvc_usb_topology_video_usb_speed=12M` 时，普通 `plain-camera-probe-summary` 显示“仍按 USB 12M full-speed 处理”，提示换高速 USB 口/线或带供电 Hub 后复测。
  - 该改动只改变普通用户可见诊断，不打开独占相机、不重置 USB、不启动建图或任何运动命令。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖 full-speed USB 场景下 probe 代理超时后，普通首屏不显示英文 abort timeout，而保留 USB full-speed 恢复动作。
- `docs/product/pc_tools_workstation.md`
  - 同步相机 probe 超时仍保留 full-speed 根因的产品合同。

## 资料来源

- 已按硬件规则读取 `docs/vendor/VENDOR_INDEX.md`。相关硬件资料入口为 Orange Pi Zero 3 用户手册和电路图：USB 接口、USB 摄像头、Type-C 供电与 USB DM/DP/VCC_USB 信号；本轮只消费既有只读诊断字段，不新增硬件接线或电气结论。

## 验证结果

- 通过：现场只读 `GET /api/robot-control/camera/mjpeg/status` 返回 `source_diagnosis_status=uvc_full_speed_usb_not_exclusive`、`source_diagnosis_not_exclusive=true`、`source_readiness=first_frame_failed`、`last_failure_reason=mjpeg_auto_retry_cooldown_after_first_frame_failure`、`exclusive_camera_claim=false`。
- 通过：现场 no-motion `POST /api/robot-control/camera/first-frame/probe` 本轮返回代理超时，但 `robot_control_executed=false`、`safe_to_control=false`。
- 通过：summary 仍保留 `live_wysiwyg_camera_recovery_next_action_plain` 和 `mapping_unblock_camera_recovery_next_action_plain` 的 USB 12M full-speed 恢复动作。
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "full-speed USB camera"`，1 file passed，1 test passed，230 skipped。
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "shows current camera probe failure"`，1 file passed，1 test passed，230 skipped。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，仅保留既有 Vite chunk size warning。
- 通过：`cd pc-tools/workstation && npm test`，3 files passed，417 tests passed。
- 通过：`git diff --check`。
- 通过：PC API 已监听 `0.0.0.0:7001`，`lsof -nP -iTCP:7001 -sTCP:LISTEN` 返回 `node 27265 ... TCP *:7001 (LISTEN)`。
- 通过：只读 summary smoke 通过 `http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 返回 `camera_source_diagnosis_status=uvc_full_speed_usb_not_exclusive`、`camera_usb_status=uvc_video_on_full_speed_usb`、`camera_usb_speed=12M`、`source_readiness=first_frame_failed`。
- 通过：构建产物包含普通用户文案，`rg -o "仍按 USB 12M full-speed|plain-camera-probe-summary|换高速 USB 口" pc-tools/workstation/dist/assets | sort | uniq -c` 命中 3 个关键片段。

## 剩余风险

- 本轮只修正 PC 普通首屏诊断优先级，不解决物理 USB full-speed 根因。
- 相机首帧仍需现场把摄像头换到高速 USB 口/线或带供电 Hub 后复测；建图启动仍缺 `camera_first_frame`。
- 完整 Nav2 行程仍待现场安全确认后重跑，并复验同窗口 wheel L/R 非零和 delivery success。
