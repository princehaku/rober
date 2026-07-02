# 目标总览短字段 DOM 化

sprint_type: micro

## 实际改动

- 普通首屏 `plain-objective-overview` 新增当前目标短字段 DOM alias：missing/blocker/ready labels、可先移动结论、建图 blocker 结论、建图是否只被相机阻塞、建图被阻塞时是否仍允许自由移动。
- 默认测试 fixture 补齐 `current_goal_*` 顶层字段，让首屏测试覆盖 live summary 同源短字段，而不是只依赖本地 checklist fallback。
- 同步更新 PC 工具文档，明确这些字段只读、不发车、不启动 Nav2/manual/keyboard/free-roam/建图/delivery/stop 或 `/cmd_vel`。

## 验证结果

- 通过：`npm test -- test/App.test.ts`，237 个测试通过。
- 通过：`npm run build`；仅保留 Vite 大 chunk 提醒。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只提升 PC 首屏目标缺口的可读和可测证据，不包含真实 HIL 动作执行。
