# PC mapping camera hardware gate

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `plain-mapping-unlock-summary` 增加相机硬件阻塞字段：是否需要硬件动作、动作标签、USB full-speed、USB 速率、是否阻塞自由移动、换线后复测顺序。
  - 字段同时兼容 summary 顶层 alias 和 `live_closure_summary`，避免旧进程/旧 fixture 首屏把硬件阻塞误显示成 false。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 full-speed USB 相机恢复用例，锁定建图解锁总览必须暴露 `换高速USB后复测`、`USB 12M`、`camera_blocks_free_move=false`、只读复测顺序，以及不启动建图/free-roam/运动。
- `docs/product/pc_tools_workstation.md`
  - 同步 `plain-mapping-unlock-summary` 作为“传感器就绪后建图”主入口的相机硬件 gate 合同。

## 验证结果

- 真实 no-motion 相机复测：
  - `POST /api/robot-control/camera/first-frame/probe?baseUrl=http://192.168.1.11:8787` 返回 `proxy_status=probe_failed`、`status=open_failed`。
  - 诊断字段为 `source_diagnosis_status=uvc_full_speed_usb_not_exclusive`、`source_diagnosis_not_exclusive=true`、`camera_usb_speed=12M`、`camera_usb_full_speed_detected=true`、`camera_hardware_action_required=true`、`camera_hardware_action_label=换高速USB后复测`。
  - 安全边界字段为 `camera_blocks_mapping_start=true`、`camera_blocks_free_move=false`、`robot_control_executed=false`、`sends_motion_when_clicked=false`、`starts_map_runtime=false`。
- `npm --prefix pc-tools/workstation test -- --run test/App.test.ts`
  - 通过：`Test Files 1 passed (1)`，`Tests 231 passed (231)`。
- `npm --prefix pc-tools/workstation run lint`
  - 通过：`eslint .` 无错误输出。
- `npm --prefix pc-tools/workstation run build`
  - 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。
  - Vite 仍提示单 bundle 超过 500 kB，这是既有体积警告，不影响本轮合同。
- `npm --prefix pc-tools/workstation test -- --run`
  - 通过：`Test Files 3 passed (3)`，`Tests 421 passed (421)`。
- PC 7001 smoke：
  - 已重启 PC 工作站到 `0.0.0.0:7001`，监听进程为 `node` PID `42639`。
  - `GET http://127.0.0.1:7001/` 返回 `200`。
  - `GET http://127.0.0.1:7001/map` 返回 `200`。
  - `GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `live_wysiwyg_missing_surface_ids=["camera"]`、`camera_hardware_action_required=true`、`camera_hardware_action_label=换高速USB后复测`、`camera_usb_speed=12M`、`camera_blocks_mapping_start=true`、`camera_blocks_free_move=false`、`mapping_start_ready=false`、`mapping_start_missing_reasons=["camera_first_frame"]`、`free_move_start_ready=true`、`radar_overlay_status=loaded`。
  - 当前 bundle `/assets/index-EqhD7nJG.js` 包含 `plain-mapping-unlock-summary`、`data-camera-hardware-action-required`、`data-camera-usb-full-speed-detected`、`data-camera-blocks-free-move` 和 `换USB后复测`。

## 剩余风险

- 真实建图仍未解锁：当前相机物理链路是 USB 12M full-speed，首帧未出。需要现场换高速 USB 口/线或带供电 USB Hub 后再复测。
- 本轮不执行真实底盘运动、不启动建图 runtime，只收紧 PC 建图解锁总览和相机硬件 gate 的 WYSIWYG 合同。
