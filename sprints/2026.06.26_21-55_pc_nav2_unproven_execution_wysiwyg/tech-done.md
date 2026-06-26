# PC Nav2 执行未证明所见即所得

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 收紧“完整 Nav2 路线执行”判断：`goal_succeeded` 和反馈样本之外，还要求 latest/execute key values 没有明确的 `nav2_goal_execution_proven=false` 或 `robot_control_executed=false`。
  - 新增“到达未证明”分支：地图终点 marker、地图行程 caption、行程进度、本轮进度、送达确认和 checklist 都会提示重新执行完整行程，而不是误写成已完成或缺反馈。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 live-shape 回归测试：`goal_succeeded + feedback_sample_count=8 + nav2_goal_execution_proven=false + robot_control_executed=false` 时，PC 必须显示 `到达未证明` 并禁止送达确认。
- `docs/product/pc_tools_workstation.md`
  - 同步记录完整 Nav2 路线执行 gate 的 WYSIWYG 收紧边界。

## 验证结果

- live 只读证据：本机 7001 代理 `GET /api/robot-control/nav2/goal/execution/latest?baseUrl=http://192.168.1.11:8787` 返回 `status=goal_succeeded`、`feedback_sample_count=8`，同时 `nav2_goal_execution_proven=false`、`robot_control_executed=false`、`delivery_success=false`。
- live 只读证据：上位机 8787 `GET /api/nav2/goal/execution/latest` 的 latest artifact 同样显示 `feedback_sample_count=8`、`delivery_success=false`，并保留未证明真车执行边界。
- 通过：`npm test -- -t "explicit unproven execution"`，结果 `1 passed / 211 skipped`。
- 通过：`npm test -- -t "route|Nav2|feedback|旧到达|缺反馈|goal_succeeded|delivery"`，结果 `64 passed / 148 skipped`。
- 通过：`npm test`，结果 `212 passed`。
- 通过：`npm run build`，Vite build 成功；保留既有 chunk size warning。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`，`node` 继续监听 `TCP *:7001 (LISTEN)`。

## 剩余风险

- 本轮只改 PC WYSIWYG 与 gate 判断；没有触发新的 Nav2 execute、没有发布 `/cmd_vel`、没有提交 delivery complete。
- 当前真实 latest 仍不能证明完整真车路线执行，因此本轮不会把 goal 标记为完成，也不会把 active goal 置为 complete。
- 本轮没有修改 Clash、系统代理或系统端口配置；项目 Node 继续使用 `0.0.0.0:7001`。
