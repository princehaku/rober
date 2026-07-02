# 当前完整行程动作 Nav2 边界 Micro Sprint

sprint_type: micro

## 实际改动

- 补齐 `current_motion_action_*` 的启动边界字段：当前完整行程动作明确会启动 Nav2 路线执行，会发运动，需要现场安全确认。
- 同步声明该动作不启动 manual、keyboard、free-roam、map runtime，不提交 delivery，也不是 stop 动作；`stop_endpoint` 只保留为兜底停止入口。
- 普通 PC 行程 gate、行程执行 gauge、执行按钮和 `plain-trip-current-motion-action` 都暴露同一组 DOM 证据，避免普通用户界面把完整行程执行和其它动作混在一起。
- 更新 PC 工作站产品文档和测试断言，保持 sprint 留档同步。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run robotControlSummary.test.ts App.test.ts`（2 files / 247 tests passed）
- 通过：`git diff --check`
- 通过：`cd pc-tools/workstation && npm run build`
- 通过：`cd pc-tools/workstation && npm run lint`

## 剩余风险

- 本轮只验证 Node/Vue 合同和 DOM 证据；未执行真实 Nav2 路线、真实底盘运动或 delivery 完成接口。
