# PC Nav2 当前服务读数动作卡合同

sprint_type: micro

## 实际改动

- 在 `action_status_cards[].id=nav2_route.evidence` 新增当前 Nav2 stack、lifecycle、planner、controller、controller requested、路线生成、路线点数和当前 blocker 数组。
- 普通首屏 `plain-action-status-card-nav2_route` 同步新增 `data-nav2-stack-running`、`data-nav2-stack-lifecycle-state`、`data-planner-server-active`、`data-controller-server-active`、`data-controller-server-requested`、`data-path-generated`、`data-nav2-path-point-count`、`data-current-blocker-reasons` 和 `data-current-blocker-labels`。
- 更新组件测试、后端 summary 测试、`docs/product/pc_tools_workstation.md` 和 `pc-tools/README.md`，明确该变化只读，不执行 Nav2、不发送 `/cmd_vel`。

## 验证结果

- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`：通过。
- `npm test -- test/catalog.test.ts -t "Robot Control summary tells the operator to rerun ROS Nav2 when PWM success lacks wheel raw L/R"`：通过。
- `npm test -- test/catalog.test.ts -t "Robot Control summary keeps current Nav2 service state separate from O11 managed execution history"`：通过。
- `npm test -- --run`：2 个测试文件、397 个测试全部通过。
- `npm run lint`：0 error，4 个既有 Vue 换行 warning。
- `npm run build`：通过，生成 `dist/assets/index-BoM72rSH.js`。
- `git diff --check`：通过。
- 本机 7001 live 验证：Node 监听 `0.0.0.0:7001`，PID `13926`；`/api/robot-control/summary` 的 `nav2_route.evidence` 返回 `nav2_stack_running=true`、`planner_server_active=true`、`controller_server_active=false`、`controller_server_requested=false`、`path_generated=true`、`nav2_path_point_count=18`；页面 bundle 包含新增 `data-controller-server-active`、`data-nav2-stack-running`、`data-nav2-path-point-count` 和 `data-current-blocker-reasons`。

## 剩余风险

- 本轮没有发送真实运动命令，也没有执行新的 Nav2 路线；当前 live 只读结果仍显示完整路线 action 成功但同窗口 wheel raw L/R 为 `0/0`，下一次发车复验必须由现场重新勾选安全确认后执行。
- live 读数显示当前 controller 未 active / 未 requested；本轮只把根因暴露到 PC 首屏，不自动恢复 controller，也不触发 Nav2 runtime。
