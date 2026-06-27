# PC Base Current Feedback Read Status

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - `readback_summary.base` 新增 `current_feedback_read_status` 和 `current_feedback_failure_reason`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 从当前 `/api/base/status` 或 `/api/status` 的 fresh `T=130` readback 提取 `serial_read` 和 `feedback_ack` 状态。
  - 当前读回 `read_error` 或 `t1001_not_observed` 时，优先覆盖 `latest_feedback_status` 和 `feedback_link_status`，避免旧 `feedback-samples/latest` 误导首屏。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `当前事实` 新增当前底盘反馈读回错误/未读到 T=1001 的说明。
  - `baseReadbackIsStaleOrEmpty` 把 `current_read_error/current_t1001_not_observed` 也视为刷新优先，不把旧 samples 当当前轮速。
- `pc-tools/workstation/test/App.test.ts`
  - 新增“当前 T=130 read error 优先于旧 wheel samples”的首屏测试，确认不会触发 manual、Nav2 execute 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 同步底盘当前读回优先口径和安全边界。

## 只读现场证据

- 只读 SSH 上位机查询显示：
  - `/api/base/feedback-samples/latest` 旧样本曾 `T=1001 observed in 3/3 samples`，但 `wheel_feedback_lr_nonzero_proven=false`。
  - `/api/status` 内当前 `base.feedback_readback.serial_read.ok=false`，错误为 `device reports readiness to read but returned no data (device disconnected or multiple access on port?)`。
  - `/api/status` 内当前 `base.feedback_ack.t1001_observed=false`。
- 本轮没有发送真实 manual、keyboard、Nav2、delivery、free-roam、stop 或 `/cmd_vel`。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "shows current base feedback read errors before stale wheel samples"`
- 通过：`npm run build`
  - TypeScript 与 Vite build 通过；仅保留既有 Vite chunk size warning。
- 通过：`npm test`
  - `2 passed`，`344 passed`
- 通过：`npm run lint`
- 通过：`git diff --check`

## 剩余风险

- 本轮只修正 PC 当前事实和 summary 优先级，不等于真实底盘反馈链路已恢复。
- 真实可动闭环仍需现场继续排查 `/dev/ttyS5` 串口占用/断连、底盘供电、底盘模式和电机使能。
