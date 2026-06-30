# PC 动作清单普通用户话术收敛

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：将普通首屏可见的 Nav2 最小预检、行程预检和 live motion runbook 文案里的 `operator report` 改为“现场报告”，保留后端 operator report 代理和 fail-closed 机制不变。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：同步前端 fallback 文案和底盘手控最小预检文案，避免普通用户区出现工程词。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/catalog.test.ts`：同步断言，并新增 `plain-live-motion-runbook` 可见文本不得包含 `operator report`。
- `docs/product/pc_tools_workstation.md`：同步普通首屏话术约束。

## 验证结果

- 已通过：`npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`，1 matched test。
- 已通过：`npm test -- --run test/robotControlSummary.test.ts`，1 file / 6 tests。
- 已通过：`npm test -- --run test/catalog.test.ts -t "minimal precheck|operator report|Nav2 execution proxy"`，1 file / 6 matched tests；随后针对失败修复又跑 `npm test -- --run test/catalog.test.ts -t "Nav2 goal preflight rejects unknown fields|Nav2 goal execution reuses minimal PC preflight|Nav2 latest execution proxy derives"`，1 file / 3 matched tests。
- 已通过：`npm run build`，`tsc` + Vite build + server `tsc` 通过；Vite 仍提示单 chunk 超过 500 kB，这是既有体积 warning。
- 已通过：`npm test -- --run`，3 files / 413 tests。
- 已通过：`npm run lint`，0 error；仍有 `RobotControlConsolePanel.vue` 4 个既有 `vue/multiline-html-element-content-newline` warning。
- 已通过：`git diff --check`。
- 已通过：重启 PC Node 到 `0.0.0.0:7001`，实际监听进程 `node` PID `90317`；只读 `GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `live_closure_summary.status=needs_wheel_rerun`、runbook/precheck/objective precheck 文案均使用“现场报告”，聚合检查 `contains_operator_report=false`、`objective_audit_sends_motion_when_clicked=false`。

## 剩余风险

- 本 sprint 只收敛 PC 普通首屏语言，不改变真实 Nav2、键盘、自由移动、建图或送达控制逻辑。
- 高级诊断、接口字段和代理实现中仍保留 `operator_report` 技术名，这是为了兼容真实上位机 API 与安全审计。
