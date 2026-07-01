# 2026-07-02 02:00 现场验收 DOM 短别名

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 在普通首屏 `plain-field-acceptance-packet` DOM 上同步暴露 summary 短 alias：
    `data-field-acceptance-primary-missing-id`、`data-field-acceptance-primary-missing-label`、
    `data-field-acceptance-primary-missing-action-id`、`data-field-acceptance-primary-readback-endpoint`、
    `data-field-acceptance-primary-readback-method`、
    `data-field-acceptance-primary-requires-motion-before-readback`、
    `data-field-acceptance-primary-requires-safety-confirm-before-motion`、
    `data-field-acceptance-primary-blocks-field-acceptance`、
    `data-live-wysiwyg-missing-reasons`、`data-mapping-start-missing-evidence`。
  - DOM 短别名优先使用 summary 顶层字段，缺省时回退到 `field_acceptance_packet` 的权威字段。
- `pc-tools/workstation/test/App.test.ts`
  - 增加普通首屏 DOM smoke 断言，锁定短 alias 不退回缺失。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步说明 summary 短 alias 也必须出现在普通首屏验收卡 DOM。

## 验证结果

- `git diff --check`：通过。
- `cd pc-tools/workstation && npm test -- --run App.test.ts robotControlSummary.test.ts`：通过，2 files / 246 tests。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过；Vite 仍提示 bundle 超 500 kB 的既有体积 warning。
- 7001 重启验证：`node` PID `19769` 监听 `*:7001`，页面 bundle 为 `index-CIVzeps6.js`。
- `curl http://127.0.0.1:7001/api/robot-control/summary | jq '{status, field_acceptance_primary_missing_id, live_wysiwyg_missing_reasons, mapping_start_missing_evidence}'`：
  - `status=needs_wheel_rerun`
  - `field_acceptance_primary_missing_id=same_window_wheel_lr_nonzero`
  - `live_wysiwyg_missing_reasons=[camera,radar_map_points]`
  - `mapping_start_missing_evidence=[camera_first_frame,lidar_fresh]`
- Live bundle 检查：`index-CIVzeps6.js` 命中 `data-field-acceptance-primary-missing-id`、`data-live-wysiwyg-missing-reasons`、`data-mapping-start-missing-evidence`。

## 剩余风险

- 本轮只补 PC 首屏 DOM 合同，没有执行 Nav2、键盘、自由移动、建图或 `/cmd_vel`。
- 运动验收仍需要现场安全确认后执行；相机首帧仍取决于真实 USB/摄像头硬件状态。
