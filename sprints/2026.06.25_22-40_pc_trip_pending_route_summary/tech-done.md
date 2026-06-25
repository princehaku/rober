# PC trip pending route summary

sprint_type: micro

## 实际改动

- 在 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 增加执行中图上目标摘要，使用刚点击的可见路线终点和当前路线点数显示 `目标 x/y；路线 n/m 个点`。
- 普通首屏行程摘要、行程状态、执行进度和地图 caption 在 Nav2 execute 请求 pending 时同步显示同一目标，和地图 `行程中` marker 对齐。
- 在 `pc-tools/workstation/test/App.test.ts` 扩展 pending Nav2 execute 测试，覆盖行程卡片和地图 caption 的 WYSIWYG 文案，并继续断言不误触 manual/delivery/cmd_vel。
- 更新 `docs/product/pc_tools_workstation.md` 记录执行中图上目标摘要的边界。

## 验证结果

- 通过：`npm test -- --testNamePattern "marks the visible route goal as executing while the plain trip request is pending"`，1 passed / 170 skipped。
- 通过：`npm run lint`。
- 通过：`npm test`，171 passed。
- 通过：`npm run build`。
- 通过：`git diff --check`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`，确认 `node` 监听 `TCP *:7001`。
- 测试副作用：`npm test` 刷新两个历史 smoke artifact 的 `checked_at`；已只还原这两个时间戳，未纳入本轮改动。

## 剩余风险

- 本轮是 PC/mock 验证，不代表真实 Nav2 已到达；真实执行仍以后端 execute 返回、latest readback 和现场 HIL 为准。
- 目标摘要只在点击后请求 pending 期间显示，若后端返回失败，仍按既有失败/复验逻辑收口。
