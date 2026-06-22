# Delivery Operator Checklist Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 将“提交送达材料并确认（高级）”从单个总确认 checkbox 改为逐项现场 checklist。
  - checklist 必须同时满足现场有人确认、周围安全、急停/停止手段就绪、观察到到达/运动、观察到停止、视频与 route/map ref 可复核、确认已投放/送达，才允许提交最终 operator report。
  - 最终 operator report 的布尔 claim 改为来自这些显式确认项；预填 ref 或送达草稿不会自动产生 `observed_motion`、`observed_stop` 或 `delivery_success`。
- `pc-tools/workstation/src/styles.css`
  - 收敛 checklist checkbox 尺寸，避免继承普通文本输入框宽度。
- `pc-tools/workstation/test/App.test.ts`
  - 补充最终送达确认未勾完整时不提交 operator report / delivery complete 的测试。
  - 补充 checklist 完整后才提交 operator report，并再调用固定 delivery complete gate 的测试。
  - 修复旧现场材料测试选择器，避免新增送达 checklist 后索引漂移。
- `docs/product/pc_tools_workstation.md`
  - 同步记录高级送达确认入口的逐项 checklist 行为和安全边界。

## 验证结果

- `npm test`
  - 通过：`Test Files 2 passed (2)`，`Tests 110 passed (110)`。
- `npm run lint`
  - 通过：`eslint .` 无报错。
- `npm run build`
  - 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。

## 剩余风险

- 本轮只改 PC 高级送达确认 UX 和前端测试，没有执行真实投放现场验收。
- 当前真实状态仍不得宣称 `delivery_success=true`；只有现场操作者逐项确认并由上位机 delivery gate 接受后，才可把送达成功作为真实证据。
- wheel raw L/R 非零仍未由本轮解决；此前 PC feedback sample 仍显示 `latest_L=0`、`latest_R=0`、`nonzero_frames=0`。
