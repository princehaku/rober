# PC Nav2 Controller 空闲解释合同

sprint_type: micro

## 实际改动

- 在 `nav2_route` 动作卡 evidence 中新增 `controller_idle_not_blocking`、`controller_blocking_current_goal` 和 `controller_idle_reason_plain`。
- 普通首屏 DOM 同步新增 `data-controller-idle-not-blocking`、`data-controller-blocking-current-goal` 和 `data-controller-idle-reason-plain`。
- 当 `controller_server_active=false` 且 `controller_server_requested=false` 时，动作卡摘要明确说明这是等待重跑的空闲读数，不是当前自动驾驶阻塞；只有 requested=true 且 active=false 才标记为当前控制服务阻塞。
- 更新 PC 工作站文档和 README，保持只读诊断口径同步。

## 验证结果

- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`：通过。
- `npm test -- test/catalog.test.ts -t "Robot Control summary tells the operator to rerun ROS Nav2 when PWM success lacks wheel raw L/R"`：通过。
- `npm test -- test/catalog.test.ts -t "Robot Control summary proxies Robot API readback endpoints and keeps commands locked"`：通过。
- `npm test -- --run`：2 个测试文件、397 个测试全部通过。
- `npm run lint`：0 error，4 个既有 Vue 换行 warning。
- `npm run build`：通过，生成 `dist/assets/index-Cm7u6hzI.js`。
- `git diff --check`：通过。
- 本机 7001 live 验证：Node 监听 `0.0.0.0:7001`，PID `29930`；`/api/robot-control/summary` 的 `nav2_route.summary_plain` 显示“控制服务当前未被请求，属于等待重跑的空闲读数，不是当前自动驾驶阻塞”，并返回 `controller_idle_not_blocking=true`、`controller_blocking_current_goal=false`。

## 剩余风险

- 本轮没有发送真实运动命令，也没有执行新的 Nav2 路线；当前 live 仍显示上次路线 action 成功但同窗口 wheel raw L/R 为 `0/0`，需要现场重新勾选安全确认后重跑 ROS 路线复验。
- 本轮只解释 controller idle 读数，不自动恢复 controller、不触发 NavigateToPose。
