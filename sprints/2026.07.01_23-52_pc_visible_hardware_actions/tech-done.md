# 2026.07.01 23:52 PC 可见设备处理动作

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 在现场验收包里新增普通用户可见的“设备处理”区域。
  - 当 `field_acceptance_hardware_actions[]` 有内容时，显示设备动作、是否阻塞建图、是否不挡自由移动，以及“换好后复测”只读按钮。
  - “换好后复测”复用相机首帧探针、MJPEG 状态和 summary 刷新链路，不启动运动或建图。
- `pc-tools/workstation/src/styles.css`
  - 为设备处理区域增加紧凑醒目样式。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖 USB full-speed 相机场景里的设备处理可见块、只读按钮和不发车属性。
  - 验证点击“换好后复测”只调用相机首帧/MJPEG/summary，不调用 Nav2、manual、free-roam、map start。
- `pc-tools/README.md`
  - 记录本轮普通首屏设备处理动作和 no-motion 边界。

## 验证结果

- 通过：`npm test -- App.test.ts -t "focuses field acceptance WYSIWYG refresh on camera only when radar and map are already visible"`
- 通过：`npm test -- App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`
- 通过：`npm test -- robotControlSummary.test.ts App.test.ts`
  - `Test Files 2 passed (2)`
  - `Tests 245 passed (245)`
- 通过：`npm run build`
  - `tsc -p tsconfig.app.json`
  - `vite build`
  - `tsc -p tsconfig.server.json`
  - Vite 仍提示既有大 chunk warning，本轮未处理拆包。
- 通过：`git diff --check`
- 通过：重启 PC Node 到 `0.0.0.0:7001`
  - `lsof` 显示 `node ... TCP *:7001 (LISTEN)`。
- 通过：只读请求 `GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787`
  - 当前真实状态：`status=needs_wheel_rerun`。
  - `field_acceptance_hardware_action_ids=["camera_usb_recovery"]`。
  - `field_acceptance_hardware_action_labels=["换高速USB后复测"]`。
  - `field_acceptance_primary_hardware_action_after_readback_endpoint=/api/robot-control/camera/first-frame/probe`。
  - `field_acceptance_primary_hardware_action_blocks_mapping_start=true`。
  - `field_acceptance_primary_hardware_action_blocks_free_move=false`。
  - `field_acceptance_packet.sends_motion_when_clicked=false`。

## 剩余风险

- 本轮不发送任何运动命令，也无法在线替用户更换 USB 口/线；真实相机恢复仍需要现场处理硬件后再点只读复测。
- 完整 Nav2 路线、键盘连续手控、自由移动和建图启动仍需要现场安全确认后再跑实车验收。
