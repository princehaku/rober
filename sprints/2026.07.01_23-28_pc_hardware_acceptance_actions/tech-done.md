# PC 设备处理动作清单

sprint_type: micro

## 实际改动

- `field_acceptance_packet` 新增 `hardware_actions[]`，把相机 USB/full-speed 设备处理从长文案升级为结构化动作。
- `camera_usb_recovery` 动作暴露：
  - 普通用户 label：`换高速USB后复测`。
  - 处理后只读复测 endpoint：`/api/robot-control/camera/first-frame/probe`。
  - `blocks_camera_wysiwyg=true`。
  - `blocks_mapping_start=true`。
  - `blocks_free_move=false`。
  - 全部不发车标志：不启动 Nav2/manual/keyboard/free-roam/map runtime/radar lifecycle，不提交 delivery，不 stop。
- `GET /api/robot-control/summary` 顶层同步暴露 `field_acceptance_hardware_action_*` 与 `field_acceptance_primary_hardware_action_*`。
- 普通首屏 `plain-field-acceptance-packet` 和 `plain-field-acceptance-remaining-actions` 同步暴露 hardware labels、after-readback endpoint、primary 和阻塞范围字段。
- `pc-tools/README.md` 同步记录该合同。

## 验证结果

- 已通过：`npm test -- robotControlSummary.test.ts App.test.ts`
  - 结果：`Test Files 2 passed (2)`，`Tests 245 passed (245)`。
- 已通过：`npm run build`
  - 结果：TypeScript app/server 和 Vite production build 通过；仅保留既有 chunk size warning。
- 已通过：`git diff --check`
  - 结果：无 whitespace error。
- 已通过：后台重启 Node 工作站并读取真实 `GET /api/robot-control/summary`
  - 监听：`0.0.0.0:7001`，PID `94247`。
  - 小车地址：`http://192.168.1.11:8787`。
  - 结果：`status=needs_wheel_rerun`，`live_wysiwyg_missing_surface_ids=["camera"]`，`camera_hardware_action_required=true`，`camera_usb_speed=12M`。
  - 结果：`field_acceptance_hardware_action_ids=["camera_usb_recovery"]`，labels 为 `["换高速USB后复测"]`。
  - 结果：处理后只读复测 endpoint 为 `["/api/robot-control/camera/first-frame/probe"]`。
  - 结果：primary 为 `camera_usb_recovery` / `换高速USB后复测`，`blocks_mapping_start=true`，`blocks_free_move=false`。
  - 结果：hardware action 全部 `sends_motion=false`，且不启动 Nav2/manual/free-roam/map runtime。

## 剩余风险

- 该改动只暴露设备处理合同，不会自动修复 USB 物理链路。
- 当前真实小车仍需现场换高速 USB 口/线或供电 Hub 后，再做相机首帧只读复测；低速自由移动不被该相机缺口阻塞。
