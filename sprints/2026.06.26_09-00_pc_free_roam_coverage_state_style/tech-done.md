# PC 扫图覆盖面板状态外框

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- 时间: 2026-06-26 09:00

## 实际改动

- 普通首屏 `扫图覆盖` 面板将 `plainFreeRoamCoverageSummary.state` 暴露为外层 `data-state`。
- 新增 `已扫出/待继续/待刷新/刷新中` 覆盖面板状态外框样式，让 map preview 的覆盖读数不只靠覆盖条和短文案表达。
- 补充前端测试，锁定已有地图画面读到 free cell 时的 `已扫出` 状态、保存后自动刷新期间仍保留旧覆盖数据的口径和 CSS 选择器。
- 更新 `docs/product/pc_tools_workstation.md`，明确该改动只影响 PC 前端 WYSIWYG，不自动刷新地图、不启动建图、不发送 manual/keyboard pulse、不执行 Nav2、delivery complete、stop 或 `/cmd_vel`。

## 验证结果

- 通过：`npm test -- -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary|keeps free-roam keyboard locked until map recording starts"`，2 passed / 190 skipped。
- 通过：`npm run lint`。
- 通过：`npm run build`。
- 通过：`npm test`，2 files passed / 192 tests passed。
- 通过：`git diff --check`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN || true`，`node` 正在监听 `*:7001`。
- 已恢复全量测试触发的两个旧 smoke artifact `checked_at` 时间戳副作用。

## 剩余风险

- 真实扫图覆盖增长、真实地图保存、真实底盘、真实键盘长按和真实 Nav2/delivery 未在本 micro sprint 中触发；本轮只做 PC 前端 mock/静态验证。
