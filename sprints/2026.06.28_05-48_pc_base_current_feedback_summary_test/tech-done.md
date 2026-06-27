# PC Base Current Feedback Summary Test

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/test/catalog.test.ts`
  - 新增 PC Node summary 层测试 `Robot Control summary keeps current T130 read errors ahead of old feedback samples`。
  - 测试模拟当前 `/api/base/status` fresh `T=130` read error，同时旧 `/api/base/feedback-samples/latest` 有 T=1001 和非零材料。
  - 锁定 `readback_summary.base.current_feedback_read_status=read_error`、`latest_feedback_status=current_read_error`、`feedback_link_status=current_t130_read_error`。
  - 确认只读 `T=130` 的 `sends_commands=true` 不进入 dangerous motion/control 字段。
- `docs/product/pc_tools_workstation.md`
  - 同步说明底盘当前读回优先级已有 PC Node summary 层回归测试覆盖。

## 验证结果

- 通过：`npm test -- --run test/catalog.test.ts -t "current T130 read errors"`
- 通过：`npm test`
  - `2 passed`，`345 passed`
- 通过：`npm run lint`
- 通过：`npm run build`
  - TypeScript 与 Vite build 通过；仅保留既有 Vite chunk size warning。
- 通过：`git diff --check`

## 剩余风险

- 本轮只补强软件回归测试，不恢复真实 `/dev/ttyS5` 或底盘 T=1001 当前读回。
- 真实可动闭环仍需现场继续排查串口占用/断连、底盘供电、底盘模式和电机使能。
