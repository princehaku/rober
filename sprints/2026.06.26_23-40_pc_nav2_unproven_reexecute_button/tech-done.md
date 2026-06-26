# 2026-06-26 23:40 PC Nav2 未证明执行的重新执行按钮

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏行程向导在已有当前图上路线、最近 Nav2 结果为 `goal_succeeded` 且有反馈但真车执行未证明时，安全确认后显示 `重新执行图上路线`。
- `pc-tools/workstation/test/App.test.ts`：补充当前路线 fixture 和断言，锁定未证明执行场景下送达仍禁用，按钮只提示重新执行，不自动调用 Nav2、delivery、manual 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`：同步记录该 UI 口径，并明确 PC 入口继续为 `0.0.0.0:7001`，不修改 Clash 或系统代理配置。

## 验证结果

- 已通过：`npm test -- test/App.test.ts -t "explicit unproven execution"`。
- 已通过：`npm test -- test/App.test.ts`，118 tests passed。
- 已通过：`npm test`，214 tests passed。
- 已通过：`npm run build`；Vite 仍有既有 chunk size warning，但构建成功。
- 已通过：`npm run lint`。
- 已通过：`git diff --check`。
- 已通过：重启本机 `npm run api`，`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node ... TCP *:7001 (LISTEN)`。
- 已通过：live `GET http://127.0.0.1:7001/api/robot-control/summary` 可读，上位机来源为 `http://192.168.1.11:8787`，连接 `readable`，当前路线 `path_generated=true`、`path_point_count=36`、`path_preview_point_count=36`，雷达预览点 8 个，机器人位姿来自 `/amcl_pose` 的 map frame。
- 已通过：live `GET http://127.0.0.1:7001/api/robot-control/nav2/goal/execution/latest` 返回 `goal_succeeded`、`feedback_sample_count=8`，但 `nav2_goal_execution_proven=false`、`robot_control_executed=false`，正好命中本轮按钮文案场景。
- 已通过：live `GET http://127.0.0.1:7001/api/robot-control/delivery/latest` 仍为 `blocked_missing_delivery_material`，送达未被本轮 UI 改动误放行。

## 剩余风险

- 本改动只优化 PC 普通首屏对“Nav2 success 但执行未证明”的下一步提示，不构成真实 HIL 送达成功。
- 轮速 L/R 非零、delivery success、真实完整路线执行、扫地式自由建图仍需继续用上车证据推进。
