# 当前建图动作边界短字段 Micro Sprint

sprint_type: micro

## 实际改动

- 补齐 `current_mapping_action_*` 合同、summary 和普通首屏 DOM：建图动作明确只启动 map runtime，不启动 Nav2/manual/keyboard/free-roam/delivery/stop。
- 补充 PC 工作站产品文档，说明 `plain-current-mapping-action` 的只读 DOM 行与实际执行边界。
- 补充 App 与 summary 测试断言，避免后续把建图动作误接到其它运动通道。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run robotControlSummary.test.ts App.test.ts`（2 files / 247 tests passed）
- 通过：`git diff --check`
- 通过：`cd pc-tools/workstation && npm run build`
- 通过：`cd pc-tools/workstation && npm run lint`

## 剩余风险

- 本轮只做 Node/Vue 合同与 DOM 证据验证，不执行真实上车 `/api/robot-control/map/start` 或任何运动接口。
