# 相机硬件动作后读回序列

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `camera_usb_recovery` 硬件动作新增 `after_action_readback_sequence`，固定为相机首帧 probe、MJPEG 状态、summary。
  - `field_acceptance_packet` 和 summary 顶层新增硬件动作读回 sequence 与 label 字段。
  - 硬件动作文案从“处理后复测相机首帧”收紧为“复测相机首帧、共享预览状态和总览”。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 设备处理卡、剩余动作卡和硬件读回按钮暴露 sequence DOM 合同。
  - 硬件动作按钮按声明的只读 sequence 执行，不再依赖单 endpoint 的隐式分支。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 补齐硬件动作读回 sequence 类型。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/robotControlSummary.test.ts`
  - 覆盖相机 USB 恢复动作的 sequence API/DOM 合同和点击路径。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录相机硬件处理后的完整只读复测链路。

## 验证结果

- `cd pc-tools/workstation && npm test -- robotControlSummary.test.ts`
  - 10 tests passed。
- `cd pc-tools/workstation && npm test -- App.test.ts`
  - 236 tests passed。
- `cd pc-tools/workstation && npm run build`
  - 通过；保留既有 Vite chunk >500KB 警告。
- `git diff --check`
  - 通过。
- `cd pc-tools/workstation && npm test -- robotControlSummary.test.ts App.test.ts catalog.test.ts`
  - 427 tests passed。
- `cd pc-tools/workstation && npm run lint`
  - 通过。
- 本机 `GET http://127.0.0.1:7001/api/robot-control/summary`
  - `field_acceptance_hardware_action_after_readback_sequences=["/api/robot-control/camera/first-frame/probe|/api/robot-control/camera/mjpeg/status|/api/robot-control/summary"]`。
  - PC Node 已重启并监听 `*:7001`。

## 剩余风险

- 本轮没有实际换 USB 口/线，也没有读取到真实相机首帧；当前真实 summary 仍显示相机在 USB 12M full-speed，阻塞画面 WYSIWYG 和建图首帧。
- 改动只保证 PC/API/DOM 的复测链路完整且只读；真实摄像头恢复仍需要现场硬件处理后再做 HIL 验收。
