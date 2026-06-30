# PC Nav2 发车前安全确认合同收敛

## sprint_type

micro

## 实际改动

- 将 PC Node 的 Nav2 preflight / execute 响应拆成 `operator_precheck_requirements` 与 `proxy_guard_requirements`：
  - 普通用户操作员预检只保留 `confirm_navigation_preflight` / `confirm_navigation_execution`。
  - `goal_limits` 与 `hard_dangerous_true_fields` 保留为代理安全护栏，不再作为普通用户额外预检表达。
- 更新普通首屏行程文案：执行图上路线发车前只要求现场安全确认；固定白名单是代理护栏。
- 更新共享 TypeScript 合同、服务端 summary/execute 返回值、前端断言和 API 合同测试。
- 同步更新 `docs/product/pc_tools_workstation.md`，明确该变化不放宽现场安全确认，也不放宽固定白名单和危险字段扫描。

## 验证结果

- 通过：`rg -n "执行图上路线只复核现场安全确认和固定白名单|只复核安全确认和固定白名单|发车前只复核安全确认|执行接口只复核安全确认和固定白名单|执行接口只复核现场安全确认和固定白名单" pc-tools/workstation/src pc-tools/workstation/test docs/product/pc_tools_workstation.md sprints/2026.07.01_06-55_pc_nav2_safety_only_precheck_contract/tech-done.md`，无旧普通用户预检文案残留。
- 通过：`git diff --check`。
- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "Nav2 goal"`，`1 passed`，`5 passed | 173 skipped`。
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "preflight|图上路线|安全确认"`，`1 passed`，`2 passed | 228 skipped`。
- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts`，`1 passed`，`6 passed`。
- 通过：`cd pc-tools/workstation && npm run build`，`tsc` 与 `vite build` 通过；Vite 仍提示单 chunk 超过 500 kB，这是既有体积提示。
- 通过：`cd pc-tools/workstation && npm run lint`。

## 剩余风险

- 本轮没有发送任何真实运动或控制 POST，没有做真实 Nav2 行程、轮速 L/R 非零、delivery success 或 HIL 验收。
- 代理固定白名单和危险字段扫描仍是硬护栏；本轮只把它们从普通用户“额外预检”文案中分离出来。
- 完整目标仍需真实车端在安全确认后验证图上路线执行、轮速复验、键盘连续手控、自由移动和建图链路。
