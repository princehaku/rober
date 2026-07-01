# 2026.07.01 23:47 PC 可见还差项目清单

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 在现场验收包里新增普通用户可见的“还差项目”区域。
  - 每个缺口行显示缺口名称、归属动作、普通读回对象，以及是否需要先完成对应动作。
  - endpoint/method/安全门禁继续保留在 DOM data 属性，普通可见文案不展示 `/api`、`proof`、`Nav2` 等工程词。
- `pc-tools/workstation/src/styles.css`
  - 为“还差项目”清单增加紧凑样式；执行后复验和可先只读复验用左边框颜色区分。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖可见“还差项目”文案、每行 DOM 字段、只读/不发车属性，以及首屏禁用工程词不外泄。
- `pc-tools/README.md`
  - 记录本轮普通首屏可见清单和 no-motion 边界。

## 验证结果

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
  - 当前缺口：`same_window_wheel_lr_nonzero`、`delivery_success`、`same_hold_window_wheel_lr_nonzero`、`stop_after_release`、`free_roam_latest_motion_ready`、`camera_first_frame`。
  - 主缺口：`field_acceptance_primary_missing_evidence_id=same_window_wheel_lr_nonzero`。
  - 主缺口动作：`field_acceptance_primary_missing_evidence_action_id=run_nav2_route`。
  - 主缺口读回：`field_acceptance_primary_missing_evidence_readback_endpoint=/api/robot-control/base/feedback-samples`。
  - `field_acceptance_packet.sends_motion_when_clicked=false`。

## 剩余风险

- 本轮仍未发送任何运动命令；完整 Nav2 路线、键盘连续手控、自由移动和建图启动需要现场安全确认后再跑实车验收。
- 可见清单来自当前 summary/readback；如果上位机状态变化，清单会随下次刷新改变。
