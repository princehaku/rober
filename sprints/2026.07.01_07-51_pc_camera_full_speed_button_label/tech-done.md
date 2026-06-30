# PC Camera Full-Speed Button Label

- sprint_type: micro
- owner: Codex mainline (subagent disabled per CEO instruction)
- time: 2026-07-01 07:51 CST

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏建图相机解锁按钮 `plain-mapping-camera-recovery-refresh` 增加 full-speed USB 专用文案。
  - 当诊断为 `uvc_full_speed_usb_not_exclusive` 或恢复文案包含 `USB 12M full-speed` / 高速 USB / 带供电 USB Hub 时，按钮和 `data-camera-recovery-action-label` 显示“换USB后复测”。
  - 普通无首帧/非 full-speed 场景继续显示“复测相机”。
- `pc-tools/workstation/test/App.test.ts`
  - 增加 DOM 回归测试，锁定 full-speed 场景的按钮文案和 no-motion 边界。
- `docs/product/pc_tools_workstation.md`
  - 同步普通首屏 full-speed 相机恢复按钮合同。

## 验证结果

- `npm test -- --run test/App.test.ts -t "mapping camera recovery|full-speed USB camera recovery"`
  - 通过：`Test Files 1 passed (1)`，`Tests 2 passed | 229 skipped (231)`。
- `npm run lint`
  - 通过。
- `npm run build`
  - 通过；仅保留既有 Vite chunk size warning。
- `npm test`
  - 通过：`Test Files 3 passed (3)`，`Tests 417 passed (417)`。
- `git diff --check`
  - 通过。
- PC 服务重启验证
  - 已重启 `npm run api`，监听 `http://0.0.0.0:7001`，PID `69745`。
- 现场只读 summary / bundle smoke
  - `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `camera_diagnosis_status=uvc_full_speed_usb_not_exclusive`、`mapping_camera_diagnosis_status=uvc_full_speed_usb_not_exclusive`。
  - `mapping_camera_next_action_plain` 明确“USB 12M full-speed，换高速 USB 口/线或带供电 USB Hub”。
  - `mapping_camera_recovery_sends_motion=false`，固定端点仍为 `/api/robot-control/camera/first-frame/probe`、`/api/robot-control/camera/mjpeg/status`、`/api/robot-control/summary`。
  - 当前 7001 前端 bundle 包含“换USB后复测”。

## 剩余风险

- 本轮只改 PC 普通首屏按钮文案和 DOM label，不执行相机首帧 probe、不打开独占相机、不启动建图、不执行 Nav2/manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。
- 真实相机仍处于 `uvc_full_speed_usb_not_exclusive`，需要现场更换高速 USB 口/线或带供电 USB Hub 后再复测首帧。
- 完整目标仍未完成：完整 Nav2 行程还缺同窗口 wheel L/R 非零复验和 delivery success；建图启动仍缺相机首帧 ready。
