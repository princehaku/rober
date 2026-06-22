# 2026-06-23 01:04 本轮进度验收卡点

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `本轮进度` 新增 `验收卡点` 单行，按轮速记录、行程执行、送达确认、键盘手控顺序显示当前第一处真实缺口。
- 当当前只读轮速已经明确为 `L/R=0/0` 时，卡点直接提示检查电机使能、供电、模式和现场空间后重试，避免现场把反馈链路可读误判成轮速非零完成。
- 该卡点只消费页面已有只读 state，不刷新接口、不执行行程、不确认送达、不发送 manual、keyboard pulse、stop 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`：补充默认首屏、L/R=0/0、行程成功但送达未完成三类卡点断言。
- `docs/product/pc_tools_workstation.md`：同步记录该只读卡点。

## 验证结果

- 只读真实上位机复核：`GET http://192.168.1.11:8787/api/base/status` 返回 `/dev/ttyS5 @ 115200`、`T=1001 observed`、最新 `L/R=0/0`、`nonzero_frame_count=0`、`wheel_feedback_lr_nonzero_proven=false`、`feedback_voltage_v=12.4223299`、`sends_motion_commands=false`、`robot_control_executed=false`。
- `npm test`：通过，`2 passed (2)`，`126 passed (126)`。
- `npm run lint`：通过，无 ESLint 报错。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只改善 PC 首屏验收卡点可读性；不证明真实 wheel raw L/R 非零、完整 Nav2 路线执行、delivery success 或 PC 键盘连续手控。
- 真实能力仍需要现场 operator 按安全口径显式执行并提供实车证据。
