# PC Nav2 Route Execution Plain Precheck

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：在 `readback_summary.nav2` 增加 `route_execution_readiness_plain` 和 `route_execution_precheck_plain`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：从只读 Nav2 proof/latest/status 派生图上路线执行/复验状态，以及最小发车前确认口径。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`：补齐默认夹具和 Nav2 路线执行回归断言。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步记录只读 summary 合同。

## 验证结果

- `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Nav2|nav2|route execution|wheel raw"`：通过，1 个文件，31 个测试通过。
- `npm --prefix pc-tools/workstation test`：通过，2 个文件，373 个测试通过。
- `npm --prefix pc-tools/workstation run build`：通过；Vite 保留既有 chunk size warning。
- 7001 本地 live 只读复验：`GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `route_execution_readiness_plain=图上路线可重跑复验；上次路线 action 成功，但同窗口 wheel raw L/R=0/0 未非零。`，`route_execution_precheck_plain=只需勾选行程前安全确认；相机、雷达和 operator report 不作为额外发车前置；执行会用 ROS 模式跑图上路线。`，同时 `safe_to_control=false`、`robot_control_executed=false`。

## 剩余风险

- 本轮只补 PC 只读字段，不执行 Nav2、不发车、不证明 wheel raw L/R 非零。
- 当前 live 仍需要 operator 勾选行程前安全确认后显式用 ROS 模式重跑图上路线，并在同窗口确认 wheel raw L/R 非零。
