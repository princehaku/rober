# O7 Realtime/Elevator Fixture Preview

## sprint_type

micro

## 实际改动

- 新增 `pc-tools/workstation/src/server/o7RealtimeElevatorPreview.ts`，实现 `GET /api/o7/realtime-elevator-preview?fixtureJson=<local-json>` 背后的 PC-only 本地 JSON fixture adapter。
- 更新 `pc-tools/workstation/src/shared/contracts.ts`，新增 `trashbot.o7.realtime_elevator_preview.v1` 输出契约，并把新 API 纳入工作站路由清单与 not_proven 边界。
- 更新 `pc-tools/workstation/src/server/catalog.ts` 与 `pc-tools/workstation/src/server/index.ts`，导出并挂载只读 API。
- 更新 `pc-tools/workstation/test/catalog.test.ts`，覆盖安全 fixture 摘要、路径脱敏、固定 false 开关，以及 missing/bad/unsupported/unsafe/success/control/realtime/tf/latency/route/elevator/floor/takeover/robot-control claim 的 fail-closed 分支。
- 更新 `docs/interfaces/o7_realtime_operator_console.md` 和 `docs/product/pc_tools_workstation.md`，同步记录 O7-KR1/KR2 fixture preview 的输入 schema、输出 schema、固定禁用字段、拒绝条件和产品边界。
- 未修改 `OKR.md`，未提升 O7 百分比。

## 验证结果

- 通过：`cd pc-tools/workstation && npm run build`
  - 关键输出：`✓ 29 modules transformed.`、`✓ built in 1.99s`
- 通过：`cd pc-tools/workstation && npm run test`
  - 关键输出：`Test Files  2 passed (2)`、`Tests  27 passed (27)`
- 通过：`cd pc-tools/workstation && npm run lint`
  - 关键输出：命令退出码 0，无 lint 报错。
- 通过：`git diff --check -- pc-tools docs/product/pc_tools_workstation.md docs/interfaces/o7_realtime_operator_console.md sprints/2026.05.27_14-15_o7-realtime-elevator-fixture-preview`
  - 关键输出：命令退出码 0，无 whitespace error。

## 剩余风险

- 本轮只证明 PC 工作站能把用户显式指定的本地 fixture 压成安全摘要；不证明真实 realtime API、ROS2 `/tf`、真实地图、真实机器人位姿、真实 <2s 延迟、真实路线成员关系、真实电梯状态链、真实楼层识别、真实人工接管或真实机器人控制。
- 未连接云端、ROS2、Nav2、硬件或电梯设备；`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false` 和所有真实连接开关保持 false。
