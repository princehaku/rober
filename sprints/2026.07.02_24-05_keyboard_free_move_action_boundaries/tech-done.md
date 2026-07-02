# 键盘与自由移动当前动作边界 Micro Sprint

sprint_type: micro

## 实际改动

- 补齐 `current_keyboard_action_*` 当前动作边界：键盘连续手控明确 `starts_keyboard=true`，启用不发车，按住才发送低速脉冲，不启动 Nav2/free-roam/建图 runtime，不提交 delivery。
- 补齐 `current_free_move_action_*` 当前动作边界：自由自助移动明确 `starts_free_roam=true`，相机和雷达不作为自由移动发车前置，不启动 Nav2/keyboard/建图 runtime，不提交 delivery。
- 普通 PC 的 `plain-keyboard-hold-gate` 和 `plain-free-move-acceptance-proof` 暴露同一组 DOM 证据，现场脚本可直接区分键盘、自由移动和建图 readiness。
- 更新 PC 工作站产品文档和测试断言。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run robotControlSummary.test.ts App.test.ts`（2 files / 247 tests passed）
- 通过：`git diff --check`
- 通过：`cd pc-tools/workstation && npm run build`
- 通过：`cd pc-tools/workstation && npm run lint`

## 剩余风险

- 本轮只验证 Node/Vue 合同与 DOM 证据，不执行真实键盘手控、自由移动 start 或 stop 接口。
