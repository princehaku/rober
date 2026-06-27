# Nav2 Controller Blocker WYSIWYG

sprint_type: micro

## 实际改动

- 将 `controller_server_active=false` 提升到 `safe_command_boundary.nav2_goal_blockers=controller_server_inactive`。
- 当路线读数/map pose 已 ready 但 controller inactive 时，`nav2_goal_ready=false` 且 label 显示 `Nav2 controller 未就绪`。
- 当路线本身未 ready 且 controller inactive 时，label 保持 `图上路线未就绪`，但 blocker 列表同时列出 controller 缺口，避免只能从中文 next_action 反推。
- 新增/扩展 catalog 回归测试，覆盖 live 旧 PWM wheel=0/0 形态和路线 ready 但 controller inactive 形态。
- 同步更新 `docs/product/pc_free_roam_mapping_design.md`。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- catalog.test.ts --testNamePattern "controller"`，1 个文件通过，1 个命中测试通过。
- 通过：`cd pc-tools/workstation && npm test`，2 个文件通过，316 个测试通过。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`；第一次 build 暴露 `nav2_goal_label` 类型 union 缺新值，补齐后通过。Vite 仍提示单 chunk 超过 500 kB 的既有体积提醒。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只修正 Nav2 controller 诊断的结构化展示，不恢复 controller lifecycle、不执行 Nav2、不发 manual/free-roam/stop 或 `/cmd_vel`。
