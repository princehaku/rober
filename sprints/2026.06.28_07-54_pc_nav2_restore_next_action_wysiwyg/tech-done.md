# PC 自动驾驶恢复后下一步 WYSIWYG 收口

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `plainTripAfterNav2LifecycleNextAction()`，自动驾驶服务启动/恢复成功后根据当前路线、地图刷新、路线可见性和 Nav2 blocker 给出下一步。
  - 恢复成功后的状态不再固定写“按地图画面确认路线”，而是落到等待路线检查、刷新地图画面确认图上路线、按当前地图确认起终点后执行，或继续处理雷达/定位缺口。
  - 新增 `nav2LifecycleRequestedMode` 记录本次点击是启动还是恢复，避免 summary 刷新后把“启动命令成功”误写成“恢复命令成功”。
  - 该逻辑只改变普通首屏向导，不改变固定 `/api/nav2/start` 和 no-motion Nav2 proof refresh 合同。
- `pc-tools/workstation/test/App.test.ts`
  - 更新 Nav2 planner/controller inactive 与 stack stopped 两条恢复测试，断言恢复/启动成功后提示“下一步：刷新地图画面确认图上路线”。
  - 继续断言恢复动作不调用 Nav2 goal execute、manual 或 `/cmd_vel`。
- `pc-tools/README.md`
  - 同步普通首屏自动驾驶恢复后的 WYSIWYG 下一步口径。
- `docs/product/pc_tools_workstation.md`
  - 同步产品文档，明确该改动不发送 NavigateToPose goal、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

## 验证结果

- `cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "shows a no-motion Nav2"`
  - 通过：`1 passed (1)`，`2 passed | 201 skipped (203)`。
  - 首轮新增断言发现 stack stopped 恢复后文案把“启动命令成功”说成“恢复命令成功”，已用 `nav2LifecycleRequestedMode` 修复并重跑通过。
- `cd pc-tools/workstation && npm test`
  - 通过：`2 passed (2)`，`351 passed (351)`。
- `cd pc-tools/workstation && npm run lint`
  - 通过：`eslint .` 无报错。
- `cd pc-tools/workstation && npm run build`
  - 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 成功；保留既有 Vite chunk size warning。
- `git diff --check`
  - 通过：无 trailing whitespace 或 patch 格式问题。

## 剩余风险

- 本轮只改 PC 普通首屏向导和软件测试，未在真实上位机上启动/恢复 Nav2 服务。
- 真实自动驾驶能否动仍要继续看上车端 planner/controller、定位、路线执行和同窗口 wheel raw L/R 非零证据。
- 旧的 `sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/*.json` 脏文件不是本轮改动，提交时保持不纳入。
