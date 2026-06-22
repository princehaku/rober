# Plain First-Jog Gate Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `canSendPlainFirstJog`，普通 `试动一下` 按钮和 `sendPlainFirstJog()` 共用同一门禁。
  - 当 latest operator report 被送达草稿覆盖，且 `恢复试动确认` 可用时，`试动一下` 直接禁用。
  - 本页刚成功提交 `记录画面` 或 `恢复试动确认` 后，允许继续调用固定 first-jog 代理；后端仍会再次读取 latest operator report 并 fail-closed。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展送达草稿覆盖场景测试：恢复前 `试动一下` 禁用，恢复成功后才解除禁用，且恢复动作本身不调用 first-jog/manual。
- `docs/product/pc_tools_workstation.md`
  - 同步记录普通 first-jog readiness gate 的行为。

## 验证结果

- `npm test`
  - 通过：`Test Files 2 passed (2)`，`Tests 111 passed (111)`。
- `npm run lint`
  - 通过：`eslint .` 无报错。
- `npm run build`
  - 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。

## 剩余风险

- 本轮没有执行真实 first-jog/manual。
- wheel raw L/R 非零仍需现场恢复试动确认后运行 during-motion 采集。
- delivery success 仍不能宣称完成。
