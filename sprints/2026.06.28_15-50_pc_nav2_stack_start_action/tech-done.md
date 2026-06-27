# 2026.06.28 15:50 PC Nav2 Stack Start Action

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 的普通行程入口新增 `nav2_stack_not_running` 识别。
- 当 `readback_summary.nav2.nav2_stack_running=false` 或 `nav2_goal_blockers` 含 `nav2_stack_not_running` 时：
  - 主执行按钮显示“先启动自动驾驶服务”；
  - 可点击服务入口显示“启动自动驾驶服务（不发车）”；
  - 当前事实条显示“自动驾驶服务未启动；先启动自动驾驶服务，再准备图上行程并按地图画面确认”。
- planner/controller inactive 仍保留“恢复规划/控制服务”的文案，不和 stack stopped 混在一起。
- `pc-tools/workstation/test/App.test.ts` 新增 stopped stack 场景，验证点击入口只调用 `/api/robot-control/nav2/start` 和 no-motion proof refresh，不调用 goal execute、base manual 或 `/cmd_vel`。
- 同步更新 `docs/product/pc_free_roam_mapping_design.md`。

## 验证结果

- `npm test -- test/App.test.ts -t 'Nav2 start action when the stack is stopped|Nav2 restore action when planner or controller is inactive'` 通过。
- `npm test` 通过，335 个测试通过。
- `npm run lint` 通过。
- `npm run build` 通过。
- `git diff --check` 通过。

## 剩余风险

- 本轮仍未点击 live “启动自动驾驶服务（不发车）”，因为没有新的现场安全确认；真实 planner/controller 启动和路线 proof 仍待现场确认后验证。
