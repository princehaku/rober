# Nav2 minimal precheck and radar refresh

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增普通雷达状态 `雷达待刷新`：`lifecycle_running=true` 但 scan proof 不新鲜/不完整时，首屏只引导 `刷新雷达`，不再展示或聚焦 `启动雷达`。
  - 行程、送达、键盘手控的下一步文案同步区分“启动雷达”和“刷新雷达”，避免真实雷达已经运行时重复启动。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - Nav2 目标预检移除 `/api/operator/report` 依赖，不再把 operator report 材料作为发车前门禁。
  - 预检仍只读固定定位/路径/Nav2 status endpoint，不调用 `/api/nav2/start`、NavigateToPose、`/cmd_vel` 或 `/api/base/manual`。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 增加 `not_required_for_nav2_minimal_safety_precheck` 状态，避免 Nav2 预检复用 stop 语义。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`
  - 覆盖“雷达运行但 proof 不完整时只刷新不启动”和“Nav2 预检不再要求 operator report”。
- `docs/product/pc_tools_workstation.md`
  - 同步 PC 普通首屏和 Nav2 最小预检口径。

## 验证结果

- `cd pc-tools/workstation && npm test -- -t "running lidar with incomplete proof"`：通过。
- `cd pc-tools/workstation && npm test -- -t "Nav2 goal preflight"`：通过。
- `cd pc-tools/workstation && npm test`：通过，2 个 test files / 152 个 tests 全部通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，Vite production build 与 server TypeScript build 完成。
- `git diff --check`：通过，无空白错误。
- `curl http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787`：通过，只读状态显示 `lifecycle_running=true`、`continuous_scan_status=latest_proof_incomplete_while_lifecycle_running`、`latest_scan_proof_fresh=false`，符合本轮“雷达待刷新”场景。
- 全量测试刷新了两个历史 DOM smoke artifact 的 `checked_at`；本轮已恢复为原始时间，未把旧证据时间戳变更纳入提交。

## 剩余风险

- 本轮不触发真实小车运动，不执行 Nav2 execute、manual、keyboard pulse、stop、delivery complete 或 `/cmd_vel`。
- “地图/画面/雷达标记所见即所得”和“像扫地机一样自由跑动然后建图”仍未完整实现；这需要单独设计前端可视化、定位/雷达 marker 数据源、自由建图安全边界和真实上位机控制策略。
