# PC Nav2 Restore Button

sprint_type: micro

## 实际改动

- PC Node 新增固定 `POST /api/robot-control/nav2/start|stop?baseUrl=...` 代理，只转发到上位机 `/api/nav2/start|stop`，浏览器 body 固定忽略，响应顶层保持 fail-closed。
- Nav2 lifecycle 代理允许 `starts_nav2=true` 作为服务恢复事实，但继续拦截 `sends_motion_commands`、`sends_base_motion_commands`、`publishes_cmd_vel`、`calls_base_manual` 和 `robot_control_executed` 等危险 true 字段。
- 普通首屏 `行程操作` 在 `nav2_goal_blockers` 明确包含 `planner_server_inactive` 或 `controller_server_inactive` 时显示 `恢复自动驾驶服务（不发车）`，并禁用主执行按钮，避免反复触发必失败的路线准备。
- 同步更新 `docs/product/pc_tools_workstation.md` 与 `docs/navigation/field_route_evidence_preflight.md`，明确该入口不是路线执行、不是 wheel raw L/R 或 delivery success 证明。

## 验证结果

- `npm test -- test/catalog.test.ts -t "Nav2 lifecycle" --maxWorkers=1 --no-fileParallelism`：通过，锁定固定 endpoint、空 body、`starts_nav2=true` 允许和运动字段 fail-closed。
- `npm test -- test/App.test.ts -t "Nav2 restore" --maxWorkers=1 --no-fileParallelism`：通过，锁定普通首屏按钮、主执行按钮禁用，以及不调用 Nav2 proof refresh、goal execute、base manual 或 `/cmd_vel`。
- `npm test -- --maxWorkers=1 --no-fileParallelism`：通过，2 个 test file、320 条测试通过。
- `npm run lint`：通过。
- `npm run build`：通过，Vite 仍提示主 chunk 超过 500 kB，这是既有体积提醒，不影响构建成功。
- `git diff --check`：通过。

## 剩余风险

- 本轮没有点击真实 live `POST /api/robot-control/nav2/start`，因为用户未在当前回合给出现场运动/服务恢复操作确认；验证边界仍是本地 mock 和合同测试。
- 恢复 Nav2 服务后，完整路线执行仍依赖后续 `/api/nav2/proof/refresh` 生成图上路线、现场安全确认、真实执行同窗口 wheel raw L/R 非零和 delivery success 证明。
